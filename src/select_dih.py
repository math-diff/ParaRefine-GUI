import json
def generate_dihedral_html(pdb_content):
    safe_pdb = json.dumps(pdb_content)
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://3dmol.org/build/3Dmol-min.js"></script>
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <style>
            /* 基础页面设置 */
            body { margin: 0; padding: 0; background-color: #ffffff; overflow: hidden; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; }
            #container { width: 100vw; height: 100vh; }
            /* UI 面板：去掉圆角和阴影，使用原生灰色调 */
            #ui-info {
                position: absolute; top: 0; left: 0; z-index: 10;
                background: #f0f0f0;
                padding: 10px;
                border-right: 1px solid #ababab;
                border-bottom: 1px solid #ababab;
                font-size: 13px;
                color: #000;
            }
            /* 按钮样式：仿原生 PyQt/Windows 样式 */
            .btn-group { margin-top: 8px; display: flex; gap: 5px; }
            button {
                cursor: pointer;
                padding: 3px 12px;
                border: 1px solid #707070;
                background-color: #e1e1e1;
                border-radius: 0px; /* 直角 */
                font-size: 12px;
                color: #000;
            }
            button:hover {
                background-color: #e5f1fb;
                border-color: #0078d4;
            }
            button:active {
                background-color: #cce4f7;
            }
            button:disabled {
                background-color: #f4f4f4;
                color: #a1a1a1;
                border: 1px solid #cccccc;
                cursor: not-allowed;
            }
            /* 选中状态文本 */
            #sel-list {
                display: block;
                margin-top: 5px;
                color: #000;
                font-family: Consolas, "Courier New", monospace;
            }
            b { font-size: 13px; }
        </style>
    </head>
    <body>
        <div id="ui-info">
            <b>Dihedral Selection:</b>
            <div style="margin-top: 3px; color: #444;">Click 4 atoms to define dihedral angle.</div>
            <span id="sel-list">Selected: None</span>
            <div class="btn-group">
                <button id="add-btn" onclick="addDihedral()" disabled>Add to List</button>
                <button id="clear-btn" onclick="clearSelection()">Clear Current</button>
            </div>
        </div>
        <div id="container"></div>
        <script>
            var selectedAtoms = [];
            var selectedAtomsData = [];
            var viewer = null;
            var bridge = null;
            // 初始化 WebChannel
            if (typeof qt !== 'undefined') {
                new QWebChannel(qt.webChannelTransport, function (channel) {
                    bridge = channel.objects.pyBridge;
                });
            }
            function updateDisplay() {
                if(!viewer) return;
                viewer.removeAllLabels();
                // 重置所有原子样式
                viewer.setStyle({}, { stick: {radius:0.15}, sphere: {scale:0.25} });
                // 高亮选中原子
                selectedAtoms.forEach(function(aid, i) {
                    var data = selectedAtomsData[i];
                    viewer.setStyle({serial: aid}, {
                        stick: {radius: 0.15},
                        sphere: {color: "red", scale: 0.35}
                    });
                    viewer.addLabel((i+1).toString(), {
                        position: {x: data.x, y: data.y, z: data.z},
                        backgroundColor: "red", backgroundOpacity: 0.9,
                        fontColor: "white", fontSize: 14
                    });
                });
                viewer.render();
                var text = selectedAtoms.length > 0 ? selectedAtoms.join("-") : "None";
                $("#sel-list").text("Selected: " + text);
                // 选满4个才启用 Add 按钮
                $("#add-btn").prop("disabled", selectedAtoms.length !== 4);
            }
            function addDihedral() {
                if (selectedAtoms.length === 4 && bridge) {
                    // 发送给 Python 处理
                    bridge.receiveAtoms(selectedAtoms.join(","));
                    // 清除当前选择
                    clearSelection();
                }
            }
            function clearSelection() {
                selectedAtoms = [];
                selectedAtomsData = [];
                updateDisplay();
            }
            $(function() {
                viewer = $3Dmol.createViewer($("#container"), { backgroundColor: "white" });
                var pdbData = ''' + safe_pdb + ''';
                viewer.addModel(pdbData, "pdb");
                viewer.zoomTo();
                viewer.setClickable({}, true, function(atom) {
                    if(!atom) return;
                    var atomID = atom.serial;
                    var idx = selectedAtoms.indexOf(atomID);
                    if (idx > -1) {
                        selectedAtoms.splice(idx, 1);
                        selectedAtomsData.splice(idx, 1);
                    } else if (selectedAtoms.length < 4) {
                        selectedAtoms.push(atomID);
                        selectedAtomsData.push({x: atom.x, y: atom.y, z: atom.z});
                    }
                    updateDisplay();
                });
                updateDisplay();
            });
        </script>
    </body>
    </html>
    '''
    return html
