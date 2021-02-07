import { FaKeyboard } from 'react-icons/fa';
import { FiMonitor, FiSpeaker } from 'react-icons/fi';
import "./App.css";

import React, { Component } from "react";
import { w3cwebsocket as W3CWebSocket } from "websocket";

const client = new W3CWebSocket('ws://127.0.0.1:8641');

const NOTIFIER_UPTIME = 2000;

export default class App extends Component {
    constructor(props){
        super(props);
        this.state = { 
            opacity: 0.0
        };
    }
    componentWillMount() {
        client.onopen = () => {
            console.log('[WS] connected');
            client.send("register");
        }
        client.onmessage = (message) => {
            let msg = JSON.parse(message.data);
            if(msg.kind == "activate_launcher"){
                console.log(msg.value)
                this.setState({
                    opacity: Math.min(1.0, msg.value)
                })
            }
        }
    }

    render() {
        return (
            <div className="App">
                <div className="Launcher" style={{ opacity: this.state.opacity}}>
                    <p>Launcher to come</p>
                </div>
            </div>
        );
    }
}
