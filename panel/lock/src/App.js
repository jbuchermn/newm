import "./App.css";

import React, { Component } from "react";
import { w3cwebsocket as W3CWebSocket } from "websocket";


const client = new W3CWebSocket("ws://127.0.0.1:8641");

export default class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user: "",
      password: "",
    };
  }
  componentWillMount() {
    client.onopen = () => {
      console.log("[WS] connected");
      client.send(JSON.stringify({ kind: "register" }));
    };
    client.onmessage = (message) => {
      let msg = JSON.parse(message.data);
      if (msg.kind == "request_auth_for_user") {
        this.setState({
          user: msg.user,
          password: ""
        });
      }
    };
  }

  handleLogin() {
    client.send(JSON.stringify({ 
      kind: "auth_for_user",
      user: this.state.user,
      password: this.state.password
    }))
  }

  render() {
    return (
      <div className="App">
        <div className="Inner">
          <div className="Row">
            <div className="title">User</div>
            <input type="text" name="name" className="textfield"
                   value={this.state.user}
                   onChange={(evt) => this.setState({ user: evt.target.value })}
                   onKeyDown={(evt) => console.log(evt)}/>
          </div>
          <div className="Row">
            <div className="title">Password</div>
            <input type="password" name="password" className="textfield"
                   value={this.state.password}
                   onChange={(evt) => this.setState({ password: evt.target.value })}
                   onKeyDown={(evt) => evt.target.key == "Enter" ? this.handleLogin() : null}/>
          </div>
        </div>
      </div>
    );
  }
}
