/*
AE Subtitle
Dockable ScriptUI panel for generating editable subtitle text layers from the active comp.
*/

(function aeSubtitlePanel(thisObj) {
    var SCRIPT_NAME = "AE Subtitle";
    var SERVER_URL = "http://127.0.0.1:8765";
    var SUBTITLE_PREFIX = "SUB ";
    var MAX_NESTED_SOURCE_DEPTH = 3;
    var SUPPORTED_SOURCE_EXTENSIONS = {
        "aif": true,
        "aiff": true,
        "aac": true,
        "avi": true,
        "flac": true,
        "m4a": true,
        "m4v": true,
        "mkv": true,
        "mov": true,
        "mp3": true,
        "mp4": true,
        "ogg": true,
        "webm": true,
        "wma": true,
        "wav": true
    };

    function buildUI(container) {
        var panel = container instanceof Panel ? container : new Window("palette", SCRIPT_NAME, undefined, { resizeable: true });
        panel.orientation = "column";
        panel.alignChildren = ["fill", "top"];
        panel.spacing = 8;
        panel.margins = 12;

        var generateButton = panel.add("button", undefined, "Generate Subtitle");
        var statusText = panel.add("statictext", undefined, "Ready");
        statusText.characters = 34;

        generateButton.onClick = function () {
            runGenerate(statusText);
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
            var comp = getActiveComp();
            var sourceCandidate = findSourceCandidate(comp);
            validateCandidateTiming(sourceCandidate);
            var sourceFile = sourceCandidate.file;
            if (!sourceFile) {
                throw new Error("No imported audio/video source file found in the active comp.");
            }

            statusText.text = "Transcribing...";
            var result = requestTranscription(sourceFile.fsName);
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

    function getActiveComp() {
        if (!app.project || !(app.project.activeItem instanceof CompItem)) {
            throw new Error("Open a comp that contains the voice-over source before generating subtitles.");
        }
        return app.project.activeItem;
    }

    function findSourceCandidate(comp) {
        var candidate;
        var selected = comp.selectedLayers;
        for (var i = 0; i < selected.length; i += 1) {
            candidate = sourceCandidateFromLayer(selected[i], 0);
            if (candidate) {
                return candidate;
            }
        }
        candidate = scanCompForSourceCandidate(comp, 0);
        if (candidate) {
            return candidate;
        }
        throw new Error(buildNoSourceLayerMessage(comp));
    }

    function scanCompForSourceCandidate(comp, depth) {
        for (var index = 1; index <= comp.numLayers; index += 1) {
            var candidate = sourceCandidateFromLayer(comp.layer(index), depth);
            if (candidate) {
                return candidate;
            }
        }
        return null;
    }

    function sourceCandidateFromLayer(layer, depth) {
        try {
            if (isUsableSourceLayer(layer)) {
                return {
                    file: layer.source.file,
                    timingLayers: [layer]
                };
            }
            if (layer && !isSubtitleLayerName(layer) && layer.source instanceof CompItem && depth < MAX_NESTED_SOURCE_DEPTH) {
                var nested = scanCompForSourceCandidate(layer.source, depth + 1);
                if (nested) {
                    nested.timingLayers.unshift(layer);
                    return nested;
                }
            }
        } catch (ignored) {
        }
        return null;
    }

    function isUsableSourceLayer(layer) {
        return layer && !isSubtitleLayerName(layer) && layer.source && layer.source.file && layer.source.file.exists && (layer.hasAudio || isLikelyMediaSource(layer.source.file));
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

    function buildNoSourceLayerMessage(comp) {
        var message = "No usable imported audio/video source layer found in the active comp.\n\n";
        message += "Put an imported audio or video file layer inside \"" + comp.name + "\" at comp time 0, then run Generate Subtitle again.";
        message += "\n\nScanned layers:";
        if (comp.numLayers === 0) {
            return message + "\n- none";
        }
        var maxLayersToShow = Math.min(comp.numLayers, 8);
        for (var index = 1; index <= maxLayersToShow; index += 1) {
            message += "\n- " + describeLayerForSourceScan(comp.layer(index));
        }
        if (comp.numLayers > maxLayersToShow) {
            message += "\n- ... " + (comp.numLayers - maxLayersToShow) + " more layer(s)";
        }
        return message;
    }

    function describeLayerForSourceScan(layer) {
        if (!layer) {
            return "Unknown layer: not available";
        }
        var name = "\"" + layer.name + "\"";
        if (isSubtitleLayerName(layer)) {
            return name + ": skipped generated subtitle layer";
        }
        try {
            if (!layer.source) {
                return name + ": no source item";
            }
            if (layer.source instanceof CompItem) {
                var nested = scanCompForSourceCandidate(layer.source, 1);
                if (nested) {
                    return name + ": nested comp contains usable source (" + nested.file.fsName + ")";
                }
                return name + ": nested comp has no usable imported audio/video source";
            }
            if (!layer.source.file) {
                return name + ": source is not an imported file";
            }
            if (!layer.source.file.exists) {
                return name + ": source file is missing on disk (" + layer.source.file.fsName + ")";
            }
            if (layer.hasAudio || isLikelyMediaSource(layer.source.file)) {
                return name + ": usable source (" + layer.source.file.fsName + ")";
            }
            return name + ": imported file is not recognized as audio/video (" + layer.source.file.fsName + ")";
        } catch (error) {
            return name + ": could not inspect layer source (" + error.message + ")";
        }
    }

    function validateCandidateTiming(candidate) {
        for (var index = 0; index < candidate.timingLayers.length; index += 1) {
            validateLayerTiming(candidate.timingLayers[index]);
        }
    }

    function validateLayerTiming(layer) {
        if (Math.abs(layer.startTime) > 0.001 || Math.abs(layer.inPoint) > 0.001 || Math.abs(layer.stretch - 100) > 0.001 || layer.timeRemapEnabled) {
            throw new Error("MVP supports source/precomp layers starting at comp time 0 with no trim, stretch, or time remap.");
        }
    }

    function requestTranscription(sourcePath) {
        var payload = "{\"source_path\":" + jsonQuote(sourcePath) + "}";
        var command = "curl -sS -X POST -H 'Content-Type: application/json' --data " + shellQuote(payload) + " " + shellQuote(SERVER_URL + "/transcribe") + " 2>&1";
        var output = system.callSystem(command);
        var response = parseJsonOutput(output);
        if (!response.ok) {
            throw new Error(response.error || output || "AE Subtitle server failed.");
        }
        if (!response.transcript_path) {
            throw new Error("AE Subtitle server did not return transcript_path.");
        }
        return response;
    }

    function shellQuote(value) {
        return "'" + String(value).replace(/'/g, "'\\''") + "'";
    }

    function jsonQuote(value) {
        return "\"" + String(value).replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\r/g, "\\r").replace(/\n/g, "\\n") + "\"";
    }

    function parseJsonOutput(output) {
        if (typeof JSON === "undefined") {
            throw new Error("After Effects JSON support is unavailable.");
        }
        var start = output.indexOf("{");
        var end = output.lastIndexOf("}");
        if (start < 0 || end < start) {
            throw new Error("AE Subtitle server did not return JSON. Open AE Subtitle.command first.\n\n" + output);
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

    var ui = buildUI(thisObj);
    if (ui instanceof Window) {
        ui.center();
        ui.show();
    }
})(this);
