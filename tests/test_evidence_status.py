"""Executable status distinctions; controls are not added research trials."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from covewm.benchmark import carrier_only_states,extract_carriers,payload_bits,render_program
from covewm.evidence_status import classify_python_evidence,collect_owned_python_execution
from covewm.tasks import TASK_BY_NAME


class EvidenceStatusTests(unittest.TestCase):
    def setUp(self):
        self.task='leap_year'
        self.source=render_program(TASK_BY_NAME[self.task].python_reference,'python',
            carrier_only_states(payload_bits(self.task,'python',0),'lexical'))

    def test_supported_proof_and_explicit_syntax_contradiction(self):
        result=classify_python_evidence(self.task,self.source)
        self.assertEqual((result.status,result.basis),('supported','restricted-AST-erasure'))
        self.assertEqual(classify_python_evidence(self.task,'def solve(').status,'contradicted')

    def test_legal_outside_grammar_is_unknown_until_complete_execution(self):
        source=render_program(TASK_BY_NAME[self.task].python_reference,'python',None).replace('    return','    pass\n    return')
        self.assertEqual(classify_python_evidence(self.task,source).status,'unavailable')
        receipt=collect_owned_python_execution(self.task,source)
        result=classify_python_evidence(self.task,source,receipt)
        self.assertEqual((result.status,result.basis),('supported','complete-bounded-execution'))

    def test_same_bits_do_not_prevent_observed_execution_contradiction(self):
        bad=self.source.replace(' = 0',' = 1 / 0',1)
        self.assertEqual(extract_carriers(self.source,'python'),extract_carriers(bad,'python'))
        self.assertEqual(classify_python_evidence(self.task,bad).status,'unavailable')
        receipt=collect_owned_python_execution(self.task,bad)
        result=classify_python_evidence(self.task,bad,receipt)
        self.assertEqual(result.status,'contradicted')
        self.assertEqual(result.first_mismatch_index,0)

    def test_stale_same_task_receipt_missing_inputs_and_wrong_contract_reject(self):
        receipt=collect_owned_python_execution(self.task,self.source)
        for source,record in ((self.source+'\n',receipt),
            (self.source,replace(receipt,outputs=receipt.outputs[:-1])),
            (self.source,replace(receipt,domain_sha256='0'*64)),
            (self.source,replace(receipt,reference_sha256='0'*64)),
            (self.source,replace(receipt,observation_rule='different observation rule')),
            (self.source,replace(receipt,runtime='different runtime'))):
            with self.subTest(source=source,record=record.runtime), self.assertRaises(ValueError):
                classify_python_evidence(self.task,source,record)


if __name__=='__main__': unittest.main()
