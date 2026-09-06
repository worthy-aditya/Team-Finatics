# Day 20 — Cross-Provider Quality Matrix (ollama `gemma4:latest` vs gemini `gemini-3.6-flash`)

| # | Mode | Scenario | Provider | Status | Sections | Invented IDs | Risk posture | Findings | Bytes | Model |
|---|------|----------|----------|--------|----------|--------------|--------------|----------|-------|-------|
| 1 | standard | benign | ollama | ✅ PASS | ✅ | ✅ none | ✅ | 4 | 7452 | gemma4:latest |

| 2 | standard | benign | gemini | ✅ PASS | ✅ | ✅ none | ✅ | 16 | 7885 | gemini-3.6-flash |

| 3 | standard | bruteforce | ollama | ✅ PASS | ✅ | ✅ none | ✅ | 5 | 8855 | gemma4:latest |

| 4 | standard | bruteforce | gemini | ✅ PASS | ✅ | ✅ none | ✅ | 12 | 9337 | gemini-3.6-flash |

| 5 | standard | incident | ollama | ✅ PASS | ✅ | ✅ none | ✅ | 5 | 9381 | gemma4:latest |

| 6 | standard | incident | gemini | ✅ PASS | ✅ | ✅ none | ✅ | 17 | 9133 | gemini-3.6-flash |

| 7 | standard | real | ollama | ✅ PASS | ✅ | ✅ none | ✅ | 8 | 10221 | gemma4:latest |

| 8 | standard | real | gemini | ✅ PASS | ✅ | ✅ none | ✅ | 20 | 10238 | gemini-3.6-flash |

| 9 | remediation | benign | ollama | ✅ PASS | ✅ | ✅ none | INFO | 4 | 5306 | gemma4:latest |

| 10 | remediation | benign | gemini | ✅ PASS | ✅ | ✅ none | INFO | 6 | 4253 | gemini-3.6-flash |

| 11 | remediation | bruteforce | ollama | ⚠ WARN | ✅ | ⚠ invented=1102 | INFO | 13 | 5561 | gemma4:latest |

| 12 | remediation | bruteforce | gemini | ✅ PASS | ✅ | ✅ none | INFO | 8 | 5658 | gemini-3.6-flash |

| 13 | remediation | incident | ollama | ✅ PASS | ✅ | ✅ none | INFO | 3 | 4694 | gemma4:latest |

| 14 | remediation | incident | gemini | ✅ PASS | ✅ | ✅ none | INFO | 8 | 5832 | gemini-3.6-flash |

| 15 | remediation | real | ollama | ✅ PASS | ✅ | ✅ none | INFO | 4 | 6341 | gemma4:latest |

| 16 | remediation | real | gemini | ✅ PASS | ✅ | ✅ none | INFO | 12 | 7448 | gemini-3.6-flash |
