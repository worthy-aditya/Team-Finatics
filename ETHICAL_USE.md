# Ethical Use Guide

SentinelAI is designed for responsible use in authorized security work. The tool is strongest when used as a controlled assessment aid, not as an unrestricted scanning utility.

## User tiers

### 1. Student / learner
Use the project to learn:

- OWASP mapping logic
- MITRE classification patterns
- report generation workflows
- defensive reasoning and remediation guidance

This tier is appropriate for labs, training, and classroom exercises on test systems.

### 2. Authorized operator / engineering reviewer
Use the tool when:

- the target system is owned by the operator or their employer
- the testing window is approved in writing
- the findings are used for remediation and improvement

This tier covers internal security reviews, engineering validation, and controlled vulnerability triage.

### 3. Bug bounty / controlled research participant
Use the tool only when:

- the scope is explicitly defined by the target owner
- the target is in a valid bug bounty program or an authorized research agreement
- the activity follows the target’s rules and boundaries

This tier requires discipline, scope control, and no unauthorized or out-of-scope testing.

## Core rule

If the user does not have explicit authorization, then the correct action is to stop and request written approval.

## Safe workflow

1. Validate consent.
2. Verify the target domain matches the expected owner.
3. Limit testing to approved hosts and valid local targets.
4. Review findings through OWASP and MITRE mappings.
5. Report only what is within scope and approved.

## Prohibited activity

- scanning arbitrary public hosts
- testing production systems without approval
- publishing raw results from third-party targets
- using the tool to evade controls or hide malicious behavior

This project is a defensive and educational tool. It should always help people secure systems, not compromise them.
