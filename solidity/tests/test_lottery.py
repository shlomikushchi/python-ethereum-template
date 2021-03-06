import os

from ethereum.tester import TransactionFailed
from test_plus.test import TestCase
import logging, sys
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
from web3 import Web3, HTTPProvider, TestRPCProvider, EthereumTesterProvider
from solc import compile_source
from web3.contract import ConciseContract

logger = logging.getLogger('.'.join(__file__.split('/')[-2:]).rstrip('.py'))

solidity_source = open(os.path.join(os.getcwd(), 'solidity', 'Lottery.sol'), 'r').read()


class TestLotterySolidity(TestCase):
    def setUp(self):
        self.contract_source_code = solidity_source
        compiled_sol = compile_source(self.contract_source_code)  # Compiled source code
        self.contract_interface = compiled_sol['<stdin>:Lottery']

        # web3.py instance
        self.w3 = Web3(EthereumTesterProvider())
        # Instantiate and deploy contract
        self.contract = self.w3.eth.contract(abi=self.contract_interface['abi'], bytecode=self.contract_interface['bin'])
        # Get transaction hash from deployed contract
        self.tx_hash = self.contract.deploy(transaction={'from': self.w3.eth.accounts[0], 'gas': 4000000})
        # Get tx receipt to get contract address
        # Contract instance in concise mode
        tx_receipt = self.w3.eth.getTransactionReceipt(self.tx_hash)
        contract_address = tx_receipt['contractAddress']
        # define it like this is an easier way to call methods, but with less power. e.g can't change from address
        self.contract_instance_concise = self.w3.eth.contract(self.contract_interface['abi'], contract_address,
                                                              ContractFactoryClass=ConciseContract)
        self.contract_instance = self.w3.eth.contract(self.contract_interface['abi'], contract_address)

    def test_make_sure_contract_is_deployed(self):
        """
        this test deploys a contract to the test provider, then checks that the transaction
        :return:
        """
        tx_receipt = self.w3.eth.getTransactionReceipt(self.tx_hash)
        contract_address = tx_receipt['contractAddress']
        print(contract_address)
        self.assertTrue(contract_address)

    def test_check_generated_accounts(self):
        """
        the web3 instance generates accounts for us, this test will verify it
        :return:
        """
        self.assertTrue(self.w3.eth.accounts)
        self.assertEqual(len(self.w3.eth.accounts), 10)

    def test_enter__success(self):
        """
        tests a successful call to enter()
        :return:
        """
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 0)
        self.contract_instance.transact({'from': self.w3.eth.accounts[0], 'value': self.w3.toWei('0.011', 'ether')}).enter()
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 1)

    def test_enter__fail_not_enough_ether(self):
        """
        expect to fail a transaction with not enough ether in the contract
        :return:
        """
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 0)
        with self.assertRaises(TransactionFailed):
            self.contract_instance.transact({'from': self.w3.eth.accounts[0],
                                             'value': self.w3.toWei('0.0099', 'ether')}).enter()
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 0)

    def test_enter__double_enter_register_once(self):
        """
        calling the enter() twice, making sure players list length is 1.
        that relies on the fact that solidity list behave like python set
        :return:
        """
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 0)
        self.contract_instance.transact({'from': self.w3.eth.accounts[0],
                                         'value': self.w3.toWei('0.011', 'ether')}).enter()
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 1)
        with self.assertRaises(TransactionFailed):
            self.contract_instance.transact({'from': self.w3.eth.accounts[0],
                                             'value': self.w3.toWei('0.011', 'ether')}).enter()
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 1)

    def test_pick_winner__players_list_is_empty_after(self):
        """
        this is checking the reset functionality of this contracr
        :return:
        """
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 0)
        self.contract_instance.transact({'from': self.w3.eth.accounts[0],
                                         'value': self.w3.toWei('0.011', 'ether')}).enter()
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 1)
        self.contract_instance.transact({'from': self.w3.eth.accounts[0]}).pickWinner()
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 0)

    def test_pick_winner__only_manager_can_call_this_method(self):
        """
        this is checking the reset functionality of this contracr
        :return:
        """
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 0)
        self.contract_instance.transact({'from': self.w3.eth.accounts[0],
                                         'value': self.w3.toWei('0.011', 'ether')}).enter()
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 1)
        with self.assertRaises(TransactionFailed):
            self.contract_instance.transact({'from': self.w3.eth.accounts[1]}).pickWinner()
        self.contract_instance.transact({'from': self.w3.eth.accounts[0]}).pickWinner()
        self.assertEqual(len(self.contract_instance_concise.getPlayers()), 0)

    def test_pick_winner__check_previous_winner_value(self):
        """
        this is checking the reset functionality of this contracr
        :return:
        """
        self.contract_instance.transact({'from': self.w3.eth.accounts[0],
                                         'value': self.w3.toWei('0.011', 'ether')}).enter()
        self.contract_instance.transact({'from': self.w3.eth.accounts[0]}).pickWinner()
        prev_winner = self.contract_instance_concise.getPreviousWinner()
        self.assertEqual(prev_winner, self.w3.eth.accounts[0])
        # now check a different winner ( address[1] )
        self.contract_instance.transact({'from':  self.w3.eth.accounts[1],
                                         'value': self.w3.toWei('0.011', 'ether')}).enter()
        self.contract_instance.transact({'from': self.w3.eth.accounts[0]}).pickWinner()
        prev_winner = self.contract_instance_concise.getPreviousWinner()
        self.assertEqual(prev_winner, self.w3.eth.accounts[1])

