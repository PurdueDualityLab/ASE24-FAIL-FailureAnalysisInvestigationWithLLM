QUESTIONS = {
        "title":            "Provide a 10 word title for the software failure incident. (return just the title)",
        "summary":          "Summarize the software failure incident. Include information about when the failure occured, what system failed, the cause of failure, the impact of failure, the responsible entity(s), and the impacted entity(s). (answer in under 250 words)",
        "time":             "When did the software failure incident happen? If possible, calculate using article published date and relative time mentioned in article.",
        "system":           "What system failed in the software failure incident? (answer in under 10 words)",
        "ResponsibleOrg":   "Which entity(s) was responsible for causing the software failure incident? (answer in under 10 words)",
        "ImpactedOrg":      "Which entity(s) was impacted by the software failure incident? (answer in under 10 words)",
        "SEcauses":         "What were the software causes of the failure incident? (answer in a list)",
        "NSEcauses":        "What were the non-software causes of the failure incident? (answer in a list)",
        "impacts":          "What happened due to the software failure incident? (answer in a list)",
        "preventions":      "What could have prevented the software failure incident? (answer in a list)", 
        "solutions":        "What could fix the software failure incident? (answer in a list)",
        "recurring":        "Was the software failure incident a recurring occurrence? If 'unknown' (option -1). If 'false' (option false). If true, then has the software failure incident occurred before 'within the same impacted entity' (option 0) or 'at other entity(s)' (option 1) or 'unknown' (option true)?",
        "references":       "From where do the articles gather information about the software failure incident? (answer in a list)",
        "phase":            "Was the software failure due to 'system design' (option 0) or 'operation' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "boundary":         "Was the software failure due to faults from 'within the system' (option 0) or from 'outside the system' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "nature":           "Was the software failure due to 'human actions' (option 0) or 'non human actions' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "dimension":        "Was the software failure due to 'hardware' (option 0) or 'software' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "objective":        "Was the software failure due to 'malicious' (option 0) or 'non-malicious' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "intent":           "Was the software failure due to 'deliberate' (option 0) or 'accidental' (option 1) fault or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "capability":       "Was the software failure 'accidental' (option 0) or due to 'development incompetence' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "duration":         "Was the software failure due to 'permanent' (option 0) or 'temporary' (option 1) or 'intermittent' (option 2) faults or 'unknown' (option -1)?",
        "domain":           "What application domain is the system: 'information' (option 0) or 'transportation' (option 1) or 'natural resources' (option 2) or 'sales' (option 3) or 'construction' (option 4) or 'manufacturing' (option 5) or 'utilities' (option 6) or 'finance' (option 7) or 'knowledge' (option 8) or 'health' (option 9) or 'entertainment' (option 10) or 'government' (option 11) or 'consumer device' (option 12) or 'multiple' (option 13) or 'other' (option 14) or 'unknown' (option -1)?",
        "cps":              "Does the system contain software that controls physical components (cyber physical system) or is it an IoT system: 'true' (option true) or 'false' (option false) or 'unknown' (option -1)?",
        "perception":       "Was the software failure due to 'sensors' (option 0) or 'actuators' (option 1) or 'processing unit' (option 2) or 'network communication' (option 3) or 'embedded software' (option 4) or 'unknown' (option -1)?",
        "communication":    "Was there a software failure at the communication level? If 'unknown' (option -1). If 'false' (option false). If true, then was the failure at the 'wired/wireless link level' (option 0) or 'connectivity level' (option 1) or 'unknown' (option true)?",
        "application":      "Was the software failure at the application level due to bugs, operating system errors, unhandled exceptions, or incorrect usage: 'true' (option true) or 'false' (option false) or 'unknown' (option -1)?",
        "behaviour":        "Was the software failure due to a 'crash' (option 0) or 'omission' (option 1) or 'timing' (option 2) or 'incorrect value' (option 3) or 'Byzantine' fault (option 4) or 'unknown' (option -1)?"
}

# TODO: Split IoT questions and only ask the questions if it is an IoT system.

# TODO: For auto prompt, split the extra instructions (ex: answer in under 10 words, etc)

TAXONOMY_OPTIONS = {
            "phase": {"0": "system design", "1": "operation", "2": "both", "3": "neither", "-1": "unknown"},
            "boundary": {"0": "within the system", "1": "outside the system", "2": "both", "3": "neither", "-1": "unknown"},
            "nature": {"0": "human actions", "1": "non human actions", "2": "both", "3": "neither", "-1": "unknown"},
            "dimension": {"0": "hardware", "1": "software", "2": "both", "3": "neither", "-1": "unknown"},
            "objective": {"0": "malicious", "1": "non-malicious", "2": "both", "3": "neither", "-1": "unknown"},
            "intent": {"0": "deliberate", "1": "accidental", "2": "both", "3": "neither", "-1": "unknown"},
            "capability": {"0": "accidental", "1": "development incompetence", "2": "both", "3": "neither", "-1": "unknown"},
            "duration": {"0": "permanent", "1": "temporary", "2": "intermittent", "-1": "unknown"},
            "domain": {"0": "information", "1": "transportation", "2": "natural resources", "3": "sales", "4": "construction", "5": "manufacturing", "6": "utilities", "7": "finance", "8": "knowledge", "9": "health", "10": "entertainment", "11": "government", "12": "consumer device", "13": "multiple", "14": "other", "-1": "unknown"},
            "cps": {"true": "true", "false": "false", "-1": "unknown"},
            "perception": {"0": "sensors", "1": "actuators", "2": "processing unit", "3": "network communication", "4": "embedded software", "-1": "unknown"},
            "communication": {"true": "true", "false": "false", "0": "wired/wireless link level", "1": "connectivity level", "-1": "unknown"},
            "application": {"true": "true", "false": "false", "-1": "unknown"},
            "behaviour": {"0": "crash", "1": "omission", "2": "timing", "3": "incorrect value", "4": "byzantine fault", "-1": "unknown"},
            "recurring": {"true": "true", "false": "false", "0": "within the same impacted entity", "1": "at other entity(s)", "-1": "unknown"},
        }

FAILURE_SYNONYMS = "hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect"