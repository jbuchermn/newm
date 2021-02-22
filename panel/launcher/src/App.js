import { FaKeyboard } from "react-icons/fa";
import { FiMonitor, FiSpeaker } from "react-icons/fi";
import "./App.css";

import React, { Component } from "react";
import { w3cwebsocket as W3CWebSocket } from "websocket";

import entries from "./entries";

const client = new W3CWebSocket("ws://127.0.0.1:8641");

const split = (arr) => {
  let res = [];
  let i = 0;
  while (arr.length > i) {
    res.push(arr.slice(i, i + 6));
    i += 6;
  }
  return res;
};

export default class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      opacity: 0.0,
      // opacity: 1.0
    };
  }
  componentWillMount() {
    client.onopen = () => {
      console.log("[WS] connected");
      client.send(JSON.stringify({ kind: "register" }));
    };
    client.onmessage = (message) => {
      let msg = JSON.parse(message.data);
      if (msg.kind == "activate_launcher") {
        this.setState({
          opacity: Math.min(1.0, msg.value),
        });
      }
    };
  }

  render() {
    return (
      <div className="App">
        <div className="Launcher" style={{ opacity: this.state.opacity }}>
          {split(entries).map((row) => (
            <div className="Row">
              {row.map((e) => (
                <div
                  className="Entry"
                  onClick={() =>
                    client.send(
                      JSON.stringify({
                        kind: "launch_app",
                        app: e.cmd,
                      })
                    )
                  }
                >
                  <img src={e.icon} />
                  <div className="Text">{e.name}</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }
}
