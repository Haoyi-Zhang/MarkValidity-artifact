"""Controls for input isolation and receiving native observation evidence."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from complete_javascript_sources import reference_source,validate_owned_source
from verify_javascript_completion import check_program,validate_observation


def execute(source,cases):
    script="const h=require(process.argv[1]);const p=JSON.parse(process.argv[2]);process.stdout.write(JSON.stringify(h.evaluateFresh(p.source,p.cases)));"
    completed=subprocess.run(['node','-e',script,str(ROOT/'js/source_completion_runner.js'),json.dumps(dict(source=source,cases=cases))],
        capture_output=True,text=True,timeout=15)
    if completed.returncode:raise ValueError(completed.stderr)
    return json.loads(completed.stdout)


class JavascriptCompletionControls(unittest.TestCase):
    def test_module_cursor_restarts_for_each_input(self):
        source='let cursor=0; function solve(x) { cursor += 1; return cursor; }'
        observed=execute(source,[[5],[99],[5]])
        self.assertEqual([json.loads(x)['value'] for x in observed['observations']],[1,1,1])
        self.assertEqual(observed['factory_initializations'],3)
        with self.assertRaises(ValueError):validate_owned_source('leap_year',source)

    def test_function_attribute_restarts_for_each_input(self):
        source='function solve(x) { solve.calls=(solve.calls||0)+1; return solve.calls; }'
        self.assertEqual([json.loads(x)['value'] for x in execute(source,[[0],[1],[0]])['observations']],[1,1,1])

    def test_exception_shaped_return_and_thrown_exception_remain_distinct(self):
        source='function solve(x) { if (x === 0) return {exception:"RangeError",message:"example"}; throw new RangeError("example"); }'
        observed=execute(source,[[0],[1]])['observations']
        self.assertNotEqual(observed[0],observed[1])
        self.assertEqual(json.loads(observed[0])['kind'],'return')
        self.assertEqual(json.loads(observed[1])['kind'],'exception')
        for value in observed:validate_observation(value)

    def test_nonfinite_output_is_not_silently_serialized_as_null(self):
        with self.assertRaisesRegex(ValueError,'outside the registered finite JSON'):
            execute('function solve(x) { return NaN; }',[[0]])

    def test_gate_accepts_saved_local_prefix_and_rejects_ambient_writes(self):
        reference=reference_source('leap_year')
        prefix='  // WM_SITE 00 LEXICAL\n  const wm_bit_00 = 0;'
        source=reference.replace('function solve(year) {\n','function solve(year) {\n'+prefix)
        self.assertEqual(validate_owned_source('leap_year',source),1)
        with self.assertRaises(ValueError):
            validate_owned_source('leap_year',source.replace('= 0;','= (globalThis.counter = 1);'))
        with self.assertRaises(ValueError):
            validate_owned_source('leap_year',source+'globalThis.counter = 1;\n')

    def test_gate_rejects_else_branch_and_reference_change(self):
        reference=reference_source('leap_year')
        source=reference.replace('function solve(year) {\n','function solve(year) {\n  // WM_SITE 00 STRUCTURAL\n  if (false) {} else { globalThis.counter = 1; }')
        with self.assertRaises(ValueError):validate_owned_source('leap_year',source)
        with self.assertRaises(ValueError):validate_owned_source('leap_year',reference.replace('% 400','% 800'))

    def test_receiver_reconstructs_mismatch_after_forged_success_flag(self):
        path=ROOT/'results/revision-native-completion/raw/grains.jsonl.gz'
        with gzip.open(path,'rt') as handle:stream=[json.loads(line) for line in handle]
        vectors={r['observation_hash']:r['observations'] for r in stream if r['type']=='observation_vector'}
        reference=next(r for r in stream if r['type']=='program' and r['role']=='reference')
        mutant=next(r for r in stream if r['type']=='program' and r['role']=='mutant')
        cases=[[n] for n in range(1,65)]
        self.assertFalse(check_program(mutant,vectors[mutant['observation_hash']],vectors[reference['observation_hash']],cases))
        forged=deepcopy(mutant);forged.update(validity='supported',mismatch_count=0,first_mismatch_index=None)
        with self.assertRaises(ValueError):
            check_program(forged,vectors[mutant['observation_hash']],vectors[reference['observation_hash']],cases)

    def test_receiver_rejects_partial_vector_and_false_fresh_input_count(self):
        path=ROOT/'results/revision-native-completion/raw/grains.jsonl.gz'
        with gzip.open(path,'rt') as handle:stream=[json.loads(line) for line in handle]
        vectors={r['observation_hash']:r['observations'] for r in stream if r['type']=='observation_vector'}
        original=next(r for r in stream if r['type']=='program' and r['role']=='reference')
        vector=vectors[original['observation_hash']];cases=[[n] for n in range(1,65)]
        with self.assertRaises(ValueError):check_program(original,vector[:-1],vector,cases)
        forged=deepcopy(original);forged['factory_initializations']=1
        with self.assertRaises(ValueError):check_program(forged,vector,vector,cases)


if __name__=='__main__':unittest.main()
