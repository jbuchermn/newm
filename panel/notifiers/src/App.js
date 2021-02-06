import "./App.css";

import React, { Component } from "react";
import { w3cwebsocket as W3CWebSocket } from "websocket";

const client = new W3CWebSocket('ws://127.0.0.1:8641');

export default class App extends Component {
    constructor(props){
        super(props);
        this.state = { 
            pressed: null,
            showingAt: null
        };
    }
    componentWillMount() {
        client.onopen = () => {
            console.log('[WS] connected');
            client.send("Hello");
        }
        client.onmessage = (message) => {
            let msg = JSON.parse(message.data);
            this.setState({ 
                pressed: msg.keyPressed,
                showingAt: new Date()
            });

            setTimeout(() => {
                if((new Date().getTime() - this.state.showingAt) < 3000) return;

                this.setState({ 
                    showingAt: null
                });
            }, 3000);
        }
    }

    render() {
        return (
            <div className="App">
                <div className={"Notifier "+(this.state.showingAt ? "up": "")}>
                    <p>{this.state.pressed}</p>
                </div>
            </div>
        );
    }
}
