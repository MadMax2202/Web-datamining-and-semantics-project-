# 04C — SWRL Reasoning Explanation

## 1. Purpose

This section demonstrates logical reasoning using SWRL rules.

SWRL stands for **Semantic Web Rule Language**. It allows us to infer new facts from existing ontology facts.

The assignment requires two reasoning demonstrations:

1. One SWRL rule on a family ontology.
2. One SWRL rule on our project knowledge base.

---

## 2. Family Ontology Reasoning

### Initial Facts

The family ontology contains three individuals:

```text
John
Mary
Alice

The initial facts are:

John parentOf Mary
Mary parentOf Alice
SWRL Rule

The rule is:

parentOf(?x, ?y) ^ parentOf(?y, ?z) -> grandparentOf(?x, ?z)
Meaning

If a person x is the parent of y, and y is the parent of z, then x is the grandparent of z.

Expected Inference

From:

John parentOf Mary
Mary parentOf Alice

The reasoner infers:

John grandparentOf Alice
Output Files
04_Reasoning_SWRL/outputs/family.owl
04_Reasoning_SWRL/outputs/family_reasoned.owl
04_Reasoning_SWRL/outputs/family_reasoning_output.txt
3. Bench Press KB Reasoning
Input KB

The project KB is loaded from:

01_Data/kb_outputs/expanded_kb.ttl

The reasoning script extracts facts of the form:

TechniqueCue affectsBiomechanics BiomechanicalConcept

Example:

grip width affectsBiomechanics range of motion
SWRL Rule

The project-specific SWRL rule is:

TechniqueCue(?cue) ^ BiomechanicalConcept(?concept) ^ affectsBiomechanics(?cue, ?concept)
-> ImportantTechniqueCue(?cue)
Meaning

If a technique cue affects a biomechanical concept, then this cue is considered an important technique cue.

Expected Inference

From a fact such as:

grip width affectsBiomechanics range of motion

The reasoner infers:

grip width rdf:type ImportantTechniqueCue
Output Files
04_Reasoning_SWRL/outputs/kb_swrl_input.owl
04_Reasoning_SWRL/outputs/kb_swrl_reasoned.owl
04_Reasoning_SWRL/outputs/kb_reasoning_output.txt
4. Why This Matters

The RDF knowledge base stores explicit facts. SWRL reasoning allows the system to infer implicit facts.

For example, the KB may explicitly state that a technique cue affects a biomechanical concept. The SWRL rule then infers that the cue is important for bench press technique.

This demonstrates the difference between:

stored knowledge
inferred knowledge
5. Reflection

The family ontology rule is simple and demonstrates classical logical reasoning.

The project-specific rule is also simple but useful because it adds semantic meaning to the bench press KB. It identifies important technique cues based on their biomechanical impact.

The main limitation is that SWRL reasoning is rule-based. It depends on manually written rules and clean ontology structure. If the extracted KB is noisy, the inferred facts can also become noisy.

For this reason, confidence scores and evidence sentences remain important in the previous KB construction step.


---

## Commands to run

From project root:

```powershell
cd C:\Users\Maxim\Documents\02_ESILV\A4\S8\Web_datamining_and_semantics\Web_Datamining_and_Semantics_Project_Maxim_Grossmann_Geoffroy_Gankoue

Run family reasoning:

python .\04_Reasoning_SWRL\04A_family_swrl_reasoning.py

Run KB reasoning:

python .\04_Reasoning_SWRL\04B_kb_swrl_reasoning.py

Expected outputs:

04_Reasoning_SWRL/outputs/family.owl
04_Reasoning_SWRL/outputs/family_reasoned.owl
04_Reasoning_SWRL/outputs/family_reasoning_output.txt
04_Reasoning_SWRL/outputs/kb_swrl_input.owl
04_Reasoning_SWRL/outputs/kb_swrl_reasoned.owl
04_Reasoning_SWRL/outputs/kb_reasoning_output.txt