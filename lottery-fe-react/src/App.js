import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import web3 from './web3';
import lottery from './lottery';


class App extends Component {
    state = {
        manager: '',
        players: [],
        balance: ''
    };

    // when the component is loaded to the page
    async componentDidMount() {
        // note: we don't need to specify the 'from' field inside the call method because
        const manager = await lottery.methods.manager().call();
        const players = await lottery.methods.getPlayers().call();
        const balance = await web3.eth.getBalance(lottery.options.address);
        this.setState({manager, players, balance});
    }

    render() {
        return (
            <div>
            <p> our manager: {this.state.manager} </p>
            </div>
    );
    }
}

export default App;
