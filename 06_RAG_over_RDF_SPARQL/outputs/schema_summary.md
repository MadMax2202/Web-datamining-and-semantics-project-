# RDF/SPARQL Schema Summary

## Namespace

```text
http://example.org/benchpress-kg/
```

## Classes

| Class | Instance count | Examples |
|---|---:|---|
| `BiomechanicalConcept` | 25 | 13.1–15.7% lateral forces, contractile force, downward force, eccentric phase, elite powerlifters |
| `DomainEntity` | 69 | 15° decline, 30° inclination, 45 pounds, about 45°, aid |
| `Equipment` | 5 | bar, bar path, bench, excessive lumbar extension, typical men’s barbell |
| `Exercise` | 5 | barbell bench press, bench press, bench press performance, decline bench press, incline bench press |
| `Joint` | 16 | elbow, elbow extension, elbow extensor moment, elbow flexion moments, greater horizontal shoulder moments |
| `KnowledgeStatement` | 0 |  |
| `Muscle` | 20 | anterior deltoid, chest and triceps development, current muscle mass, eccentric muscle action, lateral triceps |
| `TechniqueCue` | 11 | current grip, different grip widths, grip width, grip widths, medium and wide grip widths |

## Predicates

| Predicate | Count |
|---|---:|
| `ex:hasSubject` | 104 |
| `ex:hasPredicate` | 104 |
| `ex:hasObject` | 104 |
| `ex:produce_of` | 6 |
| `ex:produces` | 6 |
| `ex:perform` | 5 |
| `ex:help` | 4 |
| `ex:create` | 4 |
| `ex:influences` | 3 |
| `ex:lower` | 3 |
| `ex:give` | 3 |
| `ex:increases` | 3 |
| `ex:impose` | 3 |
| `ex:reduces` | 3 |
| `ex:cross` | 2 |
| `ex:extends` | 2 |
| `ex:create_on` | 2 |
| `ex:targetsmuscle` | 2 |
| `ex:move` | 2 |
| `ex:actsOnJoint` | 2 |
| `ex:affect_of` | 2 |
| `ex:relatedTo` | 2 |
| `ex:challenge` | 2 |
| `ex:maximize` | 1 |
| `ex:generate_in` | 1 |
| `ex:check` | 1 |
| `ex:engage` | 1 |
| `ex:shed` | 1 |
| `ex:pull` | 1 |
| `ex:support` | 1 |
| `ex:shave` | 1 |
| `ex:touch_for` | 1 |
| `ex:place` | 1 |
| `ex:address` | 1 |
| `ex:requires` | 1 |
| `ex:perform_with` | 1 |
| `ex:target_of` | 1 |
| `ex:appliesforce` | 1 |
| `ex:graze` | 1 |
| `ex:train_of` | 1 |
| `ex:flexes` | 1 |
| `ex:arch` | 1 |
| `ex:induce_in` | 1 |
| `ex:rack` | 1 |
| `ex:enter` | 1 |
| `ex:exert_of` | 1 |
| `ex:build` | 1 |
| `ex:utilize` | 1 |
| `ex:influence_of` | 1 |
| `ex:create_of` | 1 |
| `ex:involves` | 1 |
| `ex:affectsBiomechanics` | 1 |
| `ex:take` | 1 |
| `ex:investigate_of` | 1 |
| `ex:negate_of` | 1 |
| `ex:abducts` | 1 |
| `ex:weigh` | 1 |
| `ex:drive` | 1 |
| `ex:prefer` | 1 |
| `ex:aid` | 1 |
| `ex:supinate` | 1 |
| `ex:decreases` | 1 |
| `ex:equal` | 1 |
| `ex:stabilize` | 1 |
| `ex:need` | 1 |
| `ex:enable` | 1 |
| `ex:contribute` | 1 |
| `ex:influence_in` | 1 |
| `ex:demonstrate` | 1 |
| `ex:demand` | 1 |
| `ex:calculate` | 1 |

## Predicate Examples

### `ex:produce_of`

| Subject | Predicate | Object |
|---|---|---|
| `decline bench press` | `ex:produce_of` | `lower pectoralis major` |
| `passive elements` | `ex:produce_of` | `force` |
| `15° decline` | `ex:produce_of` | `lower pectoralis major` |
| `30° inclination` | `ex:produce_of` | `pectoralis major’s upper portion` |
| `incline bench press` | `ex:produce_of` | `pectoralis major’s upper portion` |

### `ex:maximize`

| Subject | Predicate | Object |
|---|---|---|
| `bench press` | `ex:maximize` | `chest and triceps development` |

### `ex:cross`

| Subject | Predicate | Object |
|---|---|---|
| `other two heads` | `ex:cross` | `elbow` |
| `long head` | `ex:cross` | `shoulder` |

### `ex:generate_in`

| Subject | Predicate | Object |
|---|---|---|
| `muscles` | `ex:generate_in` | `sticking region` |

### `ex:extends`

| Subject | Predicate | Object |
|---|---|---|
| `bar` | `ex:extends` | `elbow` |
| `triceps` | `ex:extends` | `elbow` |

### `ex:check`

| Subject | Predicate | Object |
|---|---|---|
| `first things` | `ex:check` | `wrist position` |

### `ex:create_on`

| Subject | Predicate | Object |
|---|---|---|
| `greater shoulder flexion moment` | `ex:create_on` | `proximal prime movers` |
| `narrow grip width` | `ex:create_on` | `distal prime movers` |

### `ex:engage`

| Subject | Predicate | Object |
|---|---|---|
| `bench press` | `ex:engage` | `so many muscles` |

### `ex:perform`

| Subject | Predicate | Object |
|---|---|---|
| `subjects` | `ex:perform` | `bench press` |
| `muscle` | `ex:perform` | `eccentric muscle action` |
| `elite athletes` | `ex:perform` | `valsalva maneuver` |
| `two heads` | `ex:perform` | `elbow extension` |
| `lifter` | `ex:perform` | `same testing routine` |

### `ex:influences`

| Subject | Predicate | Object |
|---|---|---|
| `bar path` | `ex:influences` | `horizontal flexion demands` |
| `total force vector` | `ex:influences` | `moments` |
| `grip width` | `ex:influences` | `horizontal flexion demands` |

### `ex:help`

| Subject | Predicate | Object |
|---|---|---|
| `technical improvements` | `ex:help` | `bench press` |
| `triceps` | `ex:help` | `both pecs` |
| `muscle irradiation` | `ex:help` | `triceps contract` |
| `triceps` | `ex:help` | `shoulder` |

### `ex:lower`

| Subject | Predicate | Object |
|---|---|---|
| `movement pattern` | `ex:lower` | `bar` |
| `next order` | `ex:lower` | `bar` |
| `descent` | `ex:lower` | `bar` |

### `ex:targetsmuscle`

| Subject | Predicate | Object |
|---|---|---|
| `triceps` | `ex:targetsmuscle` | `floor` |
| `incline press` | `ex:targetsmuscle` | `anterior deltoid` |

### `ex:shed`

| Subject | Predicate | Object |
|---|---|---|
| `article` | `ex:shed` | `light` |

### `ex:produces`

| Subject | Predicate | Object |
|---|---|---|
| `muscles` | `ex:produces` | `large enough internal extensor moments` |
| `wide grip` | `ex:produces` | `13.1–15.7% lateral forces` |
| `muscle fibers` | `ex:produces` | `most force` |
| `wide and medium grip widths` | `ex:produces` | `similar shoulder` |
| `wide and medium grip widths` | `ex:produces` | `greater horizontal shoulder moments` |

### `ex:pull`

| Subject | Predicate | Object |
|---|---|---|
| `gravity` | `ex:pull` | `bar` |

### `ex:support`

| Subject | Predicate | Object |
|---|---|---|
| `stronger arm` | `ex:support` | `load` |

### `ex:shave`

| Subject | Predicate | Object |
|---|---|---|
| `increases` | `ex:shave` | `inches` |

### `ex:touch_for`

| Subject | Predicate | Object |
|---|---|---|
| `bar` | `ex:touch_for` | `maximum muscle engagement` |

### `ex:place`

| Subject | Predicate | Object |
|---|---|---|
| `position` | `ex:place` | `shoulder` |

### `ex:give`

| Subject | Predicate | Object |
|---|---|---|
| `current grip` | `ex:give` | `most potential` |
| `stronger triceps` | `ex:give` | `aid` |
| `triceps` | `ex:give` | `extra kick` |

### `ex:address`

| Subject | Predicate | Object |
|---|---|---|
| `article` | `ex:address` | `bar path` |

### `ex:move`

| Subject | Predicate | Object |
|---|---|---|
| `scapula` | `ex:move` | `four basic ways` |
| `kinds` | `ex:move` | `furniture` |

### `ex:increases`

| Subject | Predicate | Object |
|---|---|---|
| `only factor` | `ex:increases` | `contractile force` |
| `medial triceps` | `ex:increases` | `muscle activity` |
| `lateral triceps` | `ex:increases` | `muscle activity` |

### `ex:requires`

| Subject | Predicate | Object |
|---|---|---|
| `eccentric phase` | `ex:requires` | `less shoulder horizontal abduction` |

### `ex:create`

| Subject | Predicate | Object |
|---|---|---|
| `medium grip width` | `ex:create` | `mainly vertical resultant forces` |
| `narrow grip width` | `ex:create` | `laterally directed resultant forces` |
| `medium grip width` | `ex:create` | `elbow flexion moments` |
| `wide grip width` | `ex:create` | `medially directed resultant forces` |

### `ex:perform_with`

| Subject | Predicate | Object |
|---|---|---|
| `elite powerlifters` | `ex:perform_with` | `excessive lumbar extension` |

### `ex:actsOnJoint`

| Subject | Predicate | Object |
|---|---|---|
| `triceps` | `ex:actsOnJoint` | `elbow` |
| `pectoralis major` | `ex:actsOnJoint` | `shoulder` |

### `ex:target_of`

| Subject | Predicate | Object |
|---|---|---|
| `angle` | `ex:target_of` | `muscle` |

### `ex:appliesforce`

| Subject | Predicate | Object |
|---|---|---|
| `bar` | `ex:appliesforce` | `downward force` |

### `ex:graze`

| Subject | Predicate | Object |
|---|---|---|
| `bar` | `ex:graze` | `pectoralis major` |

### `ex:train_of`

| Subject | Predicate | Object |
|---|---|---|
| `bench` | `ex:train_of` | `triceps` |

### `ex:flexes`

| Subject | Predicate | Object |
|---|---|---|
| `pectoralis major` | `ex:flexes` | `shoulder` |

### `ex:arch`

| Subject | Predicate | Object |
|---|---|---|
| `powerlifters` | `ex:arch` | `back` |

### `ex:induce_in`

| Subject | Predicate | Object |
|---|---|---|
| `maximal intended velocity training` | `ex:induce_in` | `bench press performance` |

### `ex:rack`

| Subject | Predicate | Object |
|---|---|---|
| `repeat` | `ex:rack` | `bar` |

### `ex:enter`

| Subject | Predicate | Object |
|---|---|---|
| `pectoralis major` | `ex:enter` | `stretch reflex position` |

### `ex:exert_of`

| Subject | Predicate | Object |
|---|---|---|
| `bar` | `ex:exert_of` | `force` |

### `ex:build`

| Subject | Predicate | Object |
|---|---|---|
| `barbell bench press` | `ex:build` | `serious upper-body strength` |

### `ex:affect_of`

| Subject | Predicate | Object |
|---|---|---|
| `different angles` | `ex:affect_of` | `muscle` |
| `clavicular part - sternocostal part - abdominal part` | `ex:affect_of` | `muscle` |

### `ex:impose`

| Subject | Predicate | Object |
|---|---|---|
| `triceps contract` | `ex:impose` | `lateral forces` |
| `bar` | `ex:impose` | `elbow extensor moment` |
| `bar` | `ex:impose` | `flexor` |

### `ex:utilize`

| Subject | Predicate | Object |
|---|---|---|
| `most elite lifters` | `ex:utilize` | `bar path` |

### `ex:relatedTo`

| Subject | Predicate | Object |
|---|---|---|
| `eccentric phase` | `ex:relatedTo` | `less shoulder horizontal abduction` |
| `internal moment arm` | `ex:relatedTo` | `joint angles` |

### `ex:influence_of`

| Subject | Predicate | Object |
|---|---|---|
| `different grip widths` | `ex:influence_of` | `distal prime movers` |

### `ex:create_of`

| Subject | Predicate | Object |
|---|---|---|
| `position` | `ex:create_of` | `support` |

### `ex:involves`

| Subject | Predicate | Object |
|---|---|---|
| `internal moment arm` | `ex:involves` | `joint angles` |

### `ex:reduces`

| Subject | Predicate | Object |
|---|---|---|
| `bench press` | `ex:reduces` | `workload` |
| `scapular retraction` | `ex:reduces` | `scapula` |
| `motion` | `ex:reduces` | `powerful sternoclavicular portion` |

### `ex:affectsBiomechanics`

| Subject | Predicate | Object |
|---|---|---|
| `grip width` | `ex:affectsBiomechanics` | `horizontal flexion demands` |

### `ex:challenge`

| Subject | Predicate | Object |
|---|---|---|
| `horizontal flexion demands` | `ex:challenge` | `pectoralis major` |
| `incline` | `ex:challenge` | `upper pecs` |

### `ex:take`

| Subject | Predicate | Object |
|---|---|---|
| `hand-off` | `ex:take` | `bar` |

### `ex:investigate_of`

| Subject | Predicate | Object |
|---|---|---|
| `horizontal forces` | `ex:investigate_of` | `horizontal force component` |

### `ex:negate_of`

| Subject | Predicate | Object |
|---|---|---|
| `technique` | `ex:negate_of` | `shoulder flexion demands` |

### `ex:abducts`

| Subject | Predicate | Object |
|---|---|---|
| `upper arms` | `ex:abducts` | `about 45°` |

### `ex:weigh`

| Subject | Predicate | Object |
|---|---|---|
| `typical men’s barbell` | `ex:weigh` | `45 pounds` |

### `ex:drive`

| Subject | Predicate | Object |
|---|---|---|
| `most novice lifters` | `ex:drive` | `bar` |

### `ex:prefer`

| Subject | Predicate | Object |
|---|---|---|
| `few people` | `ex:prefer` | `retraction` |

### `ex:aid`

| Subject | Predicate | Object |
|---|---|---|
| `triceps` | `ex:aid` | `pectoralis major` |

### `ex:supinate`

| Subject | Predicate | Object |
|---|---|---|
| `many people` | `ex:supinate` | `forearms` |

### `ex:decreases`

| Subject | Predicate | Object |
|---|---|---|
| `medium and wide grip widths` | `ex:decreases` | `shoulder extension moments` |

### `ex:equal`

| Subject | Predicate | Object |
|---|---|---|
| `more weight` | `ex:equal` | `more muscle` |

### `ex:stabilize`

| Subject | Predicate | Object |
|---|---|---|
| `assists` | `ex:stabilize` | `torso` |

### `ex:need`

| Subject | Predicate | Object |
|---|---|---|
| `force` | `ex:need` | `little further explanation` |

### `ex:enable`

| Subject | Predicate | Object |
|---|---|---|
| `wide and medium grip widths` | `ex:enable` | `more load` |

### `ex:contribute`

| Subject | Predicate | Object |
|---|---|---|
| `triceps` | `ex:contribute` | `anything` |

### `ex:influence_in`

| Subject | Predicate | Object |
|---|---|---|
| `kinematic factors` | `ex:influence_in` | `injury risk` |

### `ex:demonstrate`

| Subject | Predicate | Object |
|---|---|---|
| `grip widths` | `ex:demonstrate` | `similar horizontal forces` |

### `ex:demand`

| Subject | Predicate | Object |
|---|---|---|
| `shoulder flexion` | `ex:demand` | `peak` |

### `ex:calculate`

| Subject | Predicate | Object |
|---|---|---|
| `internal moments` | `ex:calculate` | `same way` |

## NL→SPARQL Guidance

Use only the namespace and predicates listed above when generating SPARQL queries.
Always include:

```sparql
PREFIX ex: <http://example.org/benchpress-kg/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
```