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
            pressed: null,
            showingAt: null
        };
    }
    componentWillMount() {
        client.onopen = () => {
            console.log('[WS] connected');
            client.send("register");
        }
        client.onmessage = (message) => {
            let msg = JSON.parse(message.data);
            console.log(msg);
            if(msg.kind == "sys_backend"){
                let icon = null;
                let value = 0;

                if(msg.backlight != undefined){
                    icon = "backlight";
                    value = msg.backlight;
                }else if(msg.kbdlight != undefined){
                    icon = "kbdlight";
                    value = msg.kbdlight;
                }else if(msg.volume != undefined){
                    icon = "volume";
                    value = msg.volume;
                }else if(msg.battery != undefined){
                    icon = "battery";
                    value = msg.battery;
                }

                value = Math.round(10 * value);

                this.setState({ 
                    icon,
                    value,
                    releaseAt: new Date().getTime() + NOTIFIER_UPTIME
                });

                setTimeout(() => {
                    if(new Date().getTime() < this.state.releaseAt) return;

                    this.setState({ 
                        releaseAt: null
                    });
                }, NOTIFIER_UPTIME + 200);
            }
        }
    }

    render() {
        return (
            <div className="App">
                <div className={"Notifier "+(this.state.releaseAt ? "up": "")}>
                    {this.state.icon == "backlight" && <FiMonitor size={400}/>}
                    {this.state.icon == "kbdlight" && <FaKeyboard size={400}/>}
                    {this.state.icon == "volume" && <FiSpeaker size={400}/>}
                    <p>{this.state.value} / 10</p>
                </div>
            </div>
        );
    }
}
