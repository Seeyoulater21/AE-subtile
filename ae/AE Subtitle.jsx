/*
AE Subtitle
Dockable ScriptUI panel for generating editable subtitle text layers from a Voice-over comp.
*/

(function aeSubtitlePanel(thisObj) {
    var SCRIPT_NAME = "AE Subtitle";
    var SETTINGS_SECTION = "AE Subtitle";
    var SUBTITLE_PREFIX = "SUB ";
    var VOICE_OVER_COMP_NAME = "Voice-over";
    var SUPPORTED_SOURCE_EXTENSIONS = {
        "aif": true,
        "aiff": true,
        "avi": true,
        "m4a": true,
        "m4v": true,
        "mkv": true,
        "mov": true,
        "mp3": true,
        "mp4": true,
        "wav": true
    };

    function buildUI(container) {
        var panel = container instanceof Panel ? container : new Window("palette", SCRIPT_NAME, undefined, { resizeable: true });
        panel.orientation = "column";
        panel.alignChildren = ["fill", "top"];
        panel.spacing = 8;
        panel.margins = 12;

        var generateButton = panel.add("button", undefined, "Generate Subtitle");
        var configGroup = panel.add("group");
        configGroup.orientation = "row";
        configGroup.alignChildren = ["fill", "center"];
        var pythonButton = configGroup.add("button", undefined, "Python...");
        var cliButton = configGroup.add("button", undefined, "CLI...");
        var statusText = panel.add("statictext", undefined, "Ready");
        statusText.characters = 34;

        generateButton.onClick = function () {
            runGenerate(statusText);
        };
        pythonButton.onClick = function () {
            try {
                choosePythonExecutable();
            } catch (error) {
                alert("AE Subtitle error:\n" + error.message);
            }
        };
        cliButton.onClick = function () {
            try {
                chooseCliFile();
            } catch (error) {
                alert("AE Subtitle error:\n" + error.message);
            }
        };

        panel.layout.layout(true);
        panel.layout.resize();
        panel.onResizing = panel.onResize = function () {
            this.layout.resize();
        };
        return panel;
    }

    function runGenerate(statusText) {
        try {
            statusText.text = "Finding source...";
            var comp = getActiveVoiceOverComp();
            var sourceLayer = findSourceLayer(comp);
            validateLayerTiming(sourceLayer);
            var sourceFile = sourceFileFromLayer(sourceLayer);
            if (!sourceFile) {
                throw new Error("No imported audio/video source file found in the active comp.");
            }

            statusText.text = "Transcribing...";
            var result = runCli(sourceFile.fsName);
            var transcript = readJsonFile(result.transcript_path);
            validateTranscript(transcript);

            app.beginUndoGroup(SCRIPT_NAME);
            try {
                rebuildSubtitleLayers(comp, transcript.segments);
            } finally {
                app.endUndoGroup();
            }

            statusText.text = "Created " + transcript.segments.length + " subtitle layers";
            alert("AE Subtitle created " + transcript.segments.length + " subtitle layers.\nCache: " + result.cache_status);
        } catch (error) {
            statusText.text = "Error";
            alert("AE Subtitle error:\n" + error.message);
        }
    }

    function getActiveVoiceOverComp() {
        if (!app.project || !(app.project.activeItem instanceof CompItem)) {
            throw new Error("Open the Voice-over comp before generating subtitles.");
        }
        var comp = app.project.activeItem;
        if (comp.name !== VOICE_OVER_COMP_NAME) {
            var proceed = confirm("Active comp is \"" + comp.name + "\", not \"" + VOICE_OVER_COMP_NAME + "\".\nMVP timing uses source seconds from comp time 0. Continue?");
            if (!proceed) {
                throw new Error("Generation cancelled. Open the Voice-over comp.");
            }
        }
        return comp;
    }

    function findSourceLayer(comp) {
        var selected = comp.selectedLayers;
        for (var i = 0; i < selected.length; i += 1) {
            if (sourceFileFromLayer(selected[i])) {
                return selected[i];
            }
        }
        for (var index = 1; index <= comp.numLayers; index += 1) {
            var layer = comp.layer(index);
            if (sourceFileFromLayer(layer) && !isSubtitleLayerName(layer)) {
                return layer;
            }
        }
        throw new Error("No imported audio/video source file found in the active comp.");
    }

    function sourceFileFromLayer(layer) {
        try {
            if (layer && layer.source && layer.source.file && layer.source.file.exists && (layer.hasAudio || isLikelyMediaSource(layer.source.file))) {
                return layer.source.file;
            }
        } catch (ignored) {
        }
        return null;
    }

    function isLikelyMediaSource(file) {
        var name = String(file.name).toLowerCase();
        var dotIndex = name.lastIndexOf(".");
        if (dotIndex < 0) {
            return false;
        }
        var extension = name.substring(dotIndex + 1);
        return SUPPORTED_SOURCE_EXTENSIONS[extension] === true;
    }

    function validateLayerTiming(layer) {
        if (Math.abs(layer.startTime) > 0.001 || Math.abs(layer.inPoint) > 0.001 || Math.abs(layer.stretch - 100) > 0.001 || layer.timeRemapEnabled) {
            throw new Error("MVP supports a source layer starting at comp time 0 with no trim, stretch, or time remap.");
        }
    }

    function runCli(sourcePath) {
        var cliFile = getCliFile();
        var command = getPythonCommand() + " " + shellQuote(cliFile.fsName) + " transcribe " + shellQuote(sourcePath) + " 2>&1";
        var output = system.callSystem(command);
        var payload = parseJsonOutput(output);
        if (!payload.ok) {
            throw new Error(payload.error || output || "Python CLI failed.");
        }
        if (!payload.transcript_path) {
            throw new Error("Python CLI did not return transcript_path.");
        }
        return payload;
    }

    function getCliFile() {
        var saved = readSetting("cliPath", "");
        if (saved) {
            var savedFile = File(saved);
            if (savedFile.exists) {
                return savedFile;
            }
        }

        var panelFile = File($.fileName);
        var candidate = File(panelFile.parent.parent.fsName + "/python/aesubtitle/cli.py");
        if (candidate.exists) {
            saveSetting("cliPath", candidate.fsName);
            return candidate;
        }

        return chooseCliFile();
    }

    function chooseCliFile() {
        var file = File.openDialog("Select python/aesubtitle/cli.py", "*.py");
        if (!file) {
            throw new Error("Python CLI path is required.");
        }
        saveSetting("cliPath", file.fsName);
        return file;
    }

    function choosePythonExecutable() {
        var file = File.openDialog("Select Python executable", "*");
        if (!file) {
            return;
        }
        saveSetting("pythonPath", file.fsName);
    }

    function getPythonCommand() {
        var saved = readSetting("pythonPath", "");
        if (saved) {
            return shellQuote(saved);
        }
        return "/usr/bin/env python3";
    }

    function shellQuote(value) {
        return "'" + String(value).replace(/'/g, "'\\''") + "'";
    }

    function parseJsonOutput(output) {
        if (typeof JSON === "undefined") {
            throw new Error("After Effects JSON support is unavailable.");
        }
        var start = output.indexOf("{");
        var end = output.lastIndexOf("}");
        if (start < 0 || end < start) {
            throw new Error("Python CLI did not return JSON:\n" + output);
        }
        return JSON.parse(output.substring(start, end + 1));
    }

    function readJsonFile(path) {
        var file = File(path);
        if (!file.exists) {
            throw new Error("Transcript JSON was not created: " + path);
        }
        file.encoding = "UTF-8";
        if (!file.open("r")) {
            throw new Error("Could not open transcript JSON: " + path);
        }
        var text = file.read();
        file.close();
        return JSON.parse(text);
    }

    function validateTranscript(transcript) {
        if (!transcript || transcript.version !== "1.0" || transcript.timebase !== "source_seconds") {
            throw new Error("Transcript JSON has an unsupported format.");
        }
        if (!transcript.segments || transcript.segments.length === 0) {
            throw new Error("Transcript contains no subtitle segments.");
        }
    }

    function rebuildSubtitleLayers(comp, segments) {
        for (var index = comp.numLayers; index >= 1; index -= 1) {
            var layer = comp.layer(index);
            if (isSubtitleLayerName(layer)) {
                layer.remove();
            }
        }

        for (var segmentIndex = segments.length - 1; segmentIndex >= 0; segmentIndex -= 1) {
            createSubtitleLayer(comp, segments[segmentIndex], segmentIndex + 1);
        }
    }

    function isSubtitleLayerName(layer) {
        return layer && layer.name && layer.name.indexOf(SUBTITLE_PREFIX) === 0;
    }

    function createSubtitleLayer(comp, segment, number) {
        var textLayer = comp.layers.addText(String(segment.text));
        textLayer.name = SUBTITLE_PREFIX + padNumber(number, 3);
        textLayer.inPoint = Number(segment.start);
        textLayer.outPoint = Number(segment.end);
        applySubtitleStyle(textLayer, comp);
    }

    function applySubtitleStyle(textLayer, comp) {
        var textProp = textLayer.property("Source Text");
        var textDocument = textProp.value;
        textDocument.justification = ParagraphJustification.CENTER_JUSTIFY;
        textDocument.fontSize = Math.max(28, Math.round(comp.height * 0.055));
        textDocument.applyFill = true;
        textDocument.fillColor = [1, 1, 1];
        textDocument.applyStroke = true;
        textDocument.strokeColor = [0, 0, 0];
        textDocument.strokeWidth = Math.max(3, Math.round(comp.height * 0.004));
        textProp.setValue(textDocument);
        textLayer.property("Transform").property("Position").setValue([comp.width / 2, comp.height * 0.84]);
    }

    function padNumber(value, width) {
        var text = String(value);
        while (text.length < width) {
            text = "0" + text;
        }
        return text;
    }

    function readSetting(key, fallback) {
        if (app.settings.haveSetting(SETTINGS_SECTION, key)) {
            return app.settings.getSetting(SETTINGS_SECTION, key);
        }
        return fallback;
    }

    function saveSetting(key, value) {
        app.settings.saveSetting(SETTINGS_SECTION, key, value);
    }

    var ui = buildUI(thisObj);
    if (ui instanceof Window) {
        ui.center();
        ui.show();
    }
})(this);
