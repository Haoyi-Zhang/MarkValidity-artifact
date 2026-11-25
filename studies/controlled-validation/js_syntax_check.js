"use strict";
// Compile-only syntax check of JavaScript sources (never executed).
// Input: JSONL file of {"id": ..., "source": ...}; output: JSON {node_version, results: {id: 0|1}}.
const fs = require("fs");
const vm = require("vm");

const lines = fs.readFileSync(process.argv[2], "utf8").split("\n").filter((l) => l.length);
const results = {};
for (const line of lines) {
  const item = JSON.parse(line);
  try {
    new vm.Script(item.source, {filename: "source-attacked.js"});
    results[item.id] = 1;
  } catch (error) {
    results[item.id] = 0;
  }
}
process.stdout.write(JSON.stringify({node_version: process.version, results}));
