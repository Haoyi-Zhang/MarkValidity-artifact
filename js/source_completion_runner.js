"use strict";

/* Execute the trusted, registered finite-domain completion specification.
 * This runner is not a sandbox for arbitrary JavaScript. The Python producer
 * accepts only exact frozen reference bodies with the registered local prefix,
 * or explicitly registered owned mutant controls. A compiled factory creates a
 * new module/function instance for every input; native builtins are trusted.
 */
const fs = require("fs");
const crypto = require("crypto");
const OBSERVATION_RULE = "covewm-tagged-return-or-exception-type-and-message-canonical-json-v2";
const INITIALIZATION_RULE = "covewm-fresh-module-instance-per-input-v1";

function canonicalize(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object" && Object.getPrototypeOf(value) === Object.prototype) {
    const output = {};
    for (const key of Object.keys(value).sort()) output[key] = canonicalize(value[key]);
    return output;
  }
  throw new Error("observation is outside the registered finite JSON value model");
}
function canonicalJson(value) { return JSON.stringify(canonicalize(value)); }
function sha(value) { return crypto.createHash("sha256").update(value, "utf8").digest("hex"); }
function emit(value) { fs.writeSync(1, JSON.stringify(value) + "\n"); }

function evaluateFresh(source, cases) {
  const factory = new Function(`${source}\nreturn solve;`);
  const observations = [];
  const digest = crypto.createHash("sha256");
  const legacyDigest = crypto.createHash("sha256");
  let returns = 0, exceptions = 0;
  for (const args of cases) {
    let observation, legacy;
    try {
      const solve = factory();
      if (typeof solve !== "function") throw new Error("solve is not a function");
      const value = solve(...args);
      observation = {kind: "return", value};
      legacy = value;
      returns += 1;
    } catch (error) {
      const type = String(error.name);
      const message = String(error.message || error);
      observation = {kind: "exception", type, message};
      legacy = {exception: type, message};
      exceptions += 1;
    }
    const serialized = canonicalJson(observation);
    observations.push(serialized);
    digest.update(serialized, "utf8");
    digest.update("\n", "utf8");
    legacyDigest.update(canonicalJson(legacy), "utf8");
    legacyDigest.update("\n", "utf8");
  }
  return {observations, observation_hash: digest.digest("hex"),
    legacy_observation_hash: legacyDigest.digest("hex"), returns, exceptions,
    factory_initializations: cases.length};
}

function main() {
  if (process.argv.length !== 3) throw new Error("usage: node source_completion_runner.js SPEC.json");
  const specBytes = fs.readFileSync(process.argv[2], "utf8");
  const spec = JSON.parse(specBytes);
  if (spec.observation_rule !== OBSERVATION_RULE || spec.initialization_rule !== INITIALIZATION_RULE) {
    throw new Error("unknown observation or initialization contract");
  }
  if (sha(JSON.stringify(spec.cases)) !== spec.domain_sha256) throw new Error("domain identity mismatch");
  if (spec.cases.some(args => !Array.isArray(args) || args.some(value =>
    !(typeof value === "string" || (typeof value === "number" && Number.isSafeInteger(value)))))) {
    throw new Error("only immutable primitive arguments from the frozen domains are accepted");
  }
  emit({type: "start", task: spec.task, spec_sha256: sha(specBytes),
    node_version: process.version, v8_version: process.versions.v8,
    observation_rule: OBSERVATION_RULE, initialization_rule: INITIALIZATION_RULE,
    domain_sha256: spec.domain_sha256, reference_sha256: spec.reference_sha256,
    domain_cases: spec.cases.length, programs: spec.programs.length});
  const vectors = new Map();
  let reference = null, referenceNominal = null, candidateCount = 0, controlCount = 0, totalCalls = 0, nominalCalls = 0;
  const started = process.hrtime.bigint();
  for (const program of spec.programs) {
    if (sha(program.source) !== program.source_sha256) throw new Error("source identity mismatch");
    const programStarted = process.hrtime.bigint();
    const observed = evaluateFresh(program.source, spec.cases);
    totalCalls += observed.factory_initializations;
    const nominal = program.role === "candidate" ? null : evaluateFresh(program.source, spec.nominal_cases);
    if (nominal !== null) nominalCalls += nominal.factory_initializations;
    if (program.role === "reference") {
      if (reference !== null || program.source_sha256 !== spec.reference_sha256) {
        throw new Error("exactly one first reference is required");
      }
      reference = observed;
      referenceNominal = nominal;
    }
    if (reference === null) throw new Error("reference must be first");
    let firstMismatch = null, mismatches = 0;
    for (let index = 0; index < spec.cases.length; index += 1) {
      if (observed.observations[index] !== reference.observations[index]) {
        mismatches += 1;
        if (firstMismatch === null) firstMismatch = index;
      }
    }
    if (vectors.has(observed.observation_hash)) {
      const retained = vectors.get(observed.observation_hash);
      if (retained.length !== observed.observations.length ||
          retained.some((value, index) => value !== observed.observations[index])) {
        throw new Error("observation digest collision");
      }
    } else {
      vectors.set(observed.observation_hash, observed.observations);
      emit({type: "observation_vector", task: spec.task,
        observation_hash: observed.observation_hash,
        observations: observed.observations});
    }
    if (program.role === "candidate") candidateCount += 1;
    if (program.role === "mutant") controlCount += 1;
    emit({type: "program", task: spec.task, role: program.role, id: program.id,
      source_sha256: program.source_sha256, reference_sha256: spec.reference_sha256,
      domain_sha256: spec.domain_sha256, parse_ok: true,
      completed_cases: spec.cases.length, factory_initializations: observed.factory_initializations,
      observation_hash: observed.observation_hash,
      legacy_observation_hash: observed.legacy_observation_hash,
      return_observations: observed.returns, exception_observations: observed.exceptions,
      validity: mismatches === 0 ? "supported" : "contradicted",
      mismatch_count: mismatches, first_mismatch_index: firstMismatch,
      first_mismatch_input: firstMismatch === null ? null : spec.cases[firstMismatch],
      first_reference_observation: firstMismatch === null ? null : reference.observations[firstMismatch],
      first_candidate_observation: firstMismatch === null ? null : observed.observations[firstMismatch],
      elapsed_ms: Number(process.hrtime.bigint() - programStarted) / 1e6});
    if (nominal !== null) {
      const nominalMismatches = nominal.observations.map((value, index) =>
        value === referenceNominal.observations[index] ? null : index).filter(index => index !== null);
      emit({type: "nominal_program", task: spec.task, role: program.role, id: program.id,
        source_sha256: program.source_sha256, completed_cases: spec.nominal_cases.length,
        observations: nominal.observations, observation_hash: nominal.observation_hash,
        mismatch_count: nominalMismatches.length,
        first_mismatch_index: nominalMismatches.length === 0 ? null : nominalMismatches[0],
        nominal_equal: nominalMismatches.length === 0});
    }
  }
  emit({type: "finish", task: spec.task, candidate_sources_executed: candidateCount,
    mutant_sources_executed: controlCount, reference_sources_executed: 1,
    total_input_calls: totalCalls, nominal_input_calls: nominalCalls, unique_observation_vectors: vectors.size,
    elapsed_ms: Number(process.hrtime.bigint() - started) / 1e6,
    resource_usage: process.resourceUsage()});
}

if (require.main === module) main();
module.exports = {canonicalJson, evaluateFresh, OBSERVATION_RULE, INITIALIZATION_RULE};
