
FAILURE_SYNONYMS = "hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect"


POSTMORTEM_QUESTIONS = {
        "title":            "Provide a title describing the software failure incident.",
        "summary":          "Summarize the software failure incident. Include information about when the failure occured, what system failed, the cause of failure, the impact of failure, the responsible entity(s), and the impacted entity(s).",
        "time":             "When did the software failure incident happen?",
        "system":           "What system(s) failed in the software failure incident?",
        "ResponsibleOrg":   "Which entity(s) was responsible for causing the software failure incident?",
        "ImpactedOrg":      "Which entity(s) was impacted by the software failure incident?",
        "SEcauses":         "What were the software causes of the failure incident?",
        "NSEcauses":        "What were the non-software causes of the failure incident?",
        "impacts":          "What were the impacts due to the software failure incident?",
        "preventions":      "What could have prevented the software failure incident?", 
        "fixes":            "What could fix the software failure incident?",
        "references":       "From where do the articles gather information about the software failure incident?",
}

PROMPT_ADDITIONS = {
        "title":        {
                                "before": "",
                                "after": "\nIf available, include information about when the failure occured, what system failed, the cause of failure, the impact of failure, the responsible entity(s), and the impacted entity(s).\nTitle should be around 10 words. Return just the title.",
                        },
        "summary":      {
                                "before": "",
                                "after": "\nAnswer in under 250 words.",
                        },              
        "time":         {
                                "before": "",
                                "after": """
                                        Return in a numbered list (with citations in the format: [#, #, ...]). 

                                        If it is unknown, estimate the timeline with following steps (show the calculation):
                                        Step 1: Find 'Published on ...' date (Do not return the 'Published on ...' date).
                                        Step 2: If relative time is mentioned (ex: last November, Friday, today, etc.). Then calculate the incident timeline by subtracting from the Published on date. Example: if the article mentions that the incident occured last November, and the article was Published on 2015-06-27, then the incident occured on November 2014. (If available, atleast return the month and year.)
                                        Step 3: If the timeline cannot be estimated, then return 'unknown'
                                        """,
                        },
        "system":        {
                                "before": "",
                                "after": "\nIf specific components failed, include them. Return the system(s) and components that failed in a numbered list (with citations in the format: [#, #, ...]).",
                        },           
        "ResponsibleOrg":       {
                                "before": "",
                                "after": "\nIf available, include any background information about the entity(s) and how they contributed to the failure. Return in a numbered list (with citations in the format: [#, #, ...]).",
                        },   
        "ImpactedOrg":        {
                                "before": "",
                                "after": "\nIf available, include any background information about the entity(s) and how they were impacted by the failure. Return in a numbered list (with citations in the format: [#, #, ...]).",
                        },      
        "SEcauses":        {
                                "before": "",
                                "after": "\nDo not return non-software causes. Return in a numbered list (with citations in the format: [#, #, ...]).",
                        },         
        "NSEcauses":        {
                                "before": "",
                                "after": "\nDo not return software causes. Return in a numbered list (with citations in the format: [#, #, ...]).",
                        },        
        "impacts":        {
                                "before": "",
                                "after": "\nReturn in a numbered list (with citations in the format: [#, #, ...]).",
                        },          
        "preventions":        {
                                "before": "",
                                "after": "\nReturn in a numbered list (with citations in the format: [#, #, ...]).",
                        },      
        "fixes":        {
                                "before": "",
                                "after": "\nReturn in a numbered list (with citations in the format: [#, #, ...]).",
                        },                
        "references":        {
                                "before": "",
                                "after": "\nProvide all specific entities from where the articles gather information from. Return in a numbered list (with citations in the format: [#, #, ...]).",
                        },
        "recurring":    {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options.",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": """
                                                {
                                                "one_organization": true or false,
                                                "multiple_organization": true or false,
                                                "unknown": true or false,
                                                }
                                                """,
                                        },
                        },          
        "phase":        {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options.",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": """
                                                {
                                                "design": true or false,
                                                "operation": true or false,
                                                "unknown": true or false,
                                                }
                                                """,
                                        },
                        },            
        "boundary":     {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options.",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": """
                                                {
                                                "within_system": true or false,
                                                "outside_system": true or false,
                                                "unknown": true or false,
                                                }
                                                """,
                                        },
                        },         
        "nature":       {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options.",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": """
                                                {
                                                "non-human_actions": true or false,
                                                "human_actions": true or false,
                                                "unknown": true or false,
                                                }
                                                """,
                                        },
                        },           
        "dimension":    {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options.",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": """
                                                {
                                                "hardware": true or false,
                                                "software": true or false,
                                                "unknown": true or false,
                                                }
                                                """,
                                        },
                        },        
        "objective":    {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options.",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": """
                                                {
                                                "malicious": true or false,
                                                "non-malicious": true or false,
                                                "unknown": true or false,
                                                }
                                                """,
                                        },
                        },        
        "intent":       {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options.",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": """
                                                {
                                                "poor_decisions": true or false,
                                                "accidental_decisions": true or false,
                                                "unknown": true or false,
                                                }
                                                """,
                                        },
                        },           
        "capability":   {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options.",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": """
                                                {
                                                "development_incompetence": true or false,
                                                "accidental": true or false,
                                                "unknown": true or false,
                                                }
                                                """,
                                        },
                        },       
        "duration":     {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options.",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": """
                                                {
                                                "permanent": true or false,
                                                "temporary": true or false,
                                                "unknown": true or false,
                                                }
                                                """,
                                        },
                        }, 
        "behaviour":    {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about the six options.",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": """
                                                {
                                                "crash": true or false,
                                                "omission": true or false,
                                                "timing": true or false,
                                                "value": true or false,
                                                "byzantine": true or false,
                                                "other": true or false
                                                }
                                                """,
                                        },
                        },        
        "domain":       {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": "",
                                        },
                        },           
        "cps":          {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": "",
                                        },
                        },              
        "perception":   {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": "",
                                        },
                        },       
        "communication":{
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": "",
                                        },
                        },    
        "application":  {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": "",
                                        },
                        },            
}

TAXONOMY_DEFINITIONS = {
        "recurring":            """
                                The software failure incident having happened again at:
                                (a) one_organization: Similar incident has happened before or again within the same organization or with its products and services
                                (b) multiple_organization: Similar incident has happened before or again at other organizations or with their products and services
                                """,
        "phase":                """
                                The software failure incident occurring due to the development phases:
                                (a) design: Failure due to contributing factors introduced by system development, system updates, or procedures to operate or maintain the system
                                (b) operation: Failure due to contributing factors introduced by the operation or misuse of the system
                                """,
        "boundary":             """
                                The boundary of the software failure incident:
                                (a) within_system: Failure due to contributing factors that originate from within the system 
                                (b) outside_system: Failure due to contributing factors that originate from outside the system
                                """,
        "nature":               """
                                The software failure incident occurring due to:
                                (a) non-human_actions: Failure due to contributing factors introduced without human participation
                                (b) human_actions: Failure due to contributing factors introduced by human actions
                                """,
        "dimension":            """
                                The software failure incident occurring due to:
                                (a) hardware: Failure due to contributing factors that originate in hardware
                                (b) software: Failure due to contributing factors that originate in software
                                """,
        "objective":            """
                                The objective of the software failure incident:
                                (a) malicious: Failure due to contributing factors introduced by human(s) with intent to harm the system
                                (b) non-malicious: Failure due to contributing factors introduced without intent to harm the system
                                """,
        "intent":               """
                                The intent of the software failure incident:
                                (a) poor_decisions: Failure due to contributing factors introduced by poor decisions
                                (b) accidental_decisions: Failure due to contributing factors introduced by mistakes or unintended decisions
                                """,
        "capability":           """
                                The software failure incident occurring due to:
                                (a) development_incompetence: Failure due to contributing factors introduced due to lack of professional competence by humans or development organization
                                (b) accidental: Failure due to contributing factors introduced accidentally
                                """,
        "duration":             """
                                The duration of the software failure incident being:
                                (a) permanent: Failure due to contributing factors introduced by all circumstances
                                (b) temporary: Failure due to contributing factors introduced by certain circumstances but not all
                                """,
        "behaviour":            """
                                The behavior of the software failure incident:
                                (a) crash: Failure due to system losing state and not performing any of its intended functions
                                (b) omission: Failure due to system omitting to perform its intended functions at an instance(s)
                                (c) timing: Failure due to system performing its intended functions correctly, but too late or too early 
                                (d) value: Failure due to system performing its intended functions incorrectly
                                (e) byzantine: Failure due to system behaving erroneously with inconsistent responses and interactions
                                (f) other: Failure due to system behaving in a way not described in the (a to e) options; What is the other behaviour?
                                """,
        "domain":           ,
        "cps":              ,
        #CPS:
        "perception":       ,
        "communication":    ,
        "application":      ,
}

TAXONOMY_QUESTIONS = {
        "recurring":            """
                                (a) one: Have similar incident(s) happened before or again within the same organization or with its products and services?
                                (b) multiple: Have similar incident(s) happened before or again at other organizations or with their products and services?
                                """,
        "phase":                """
                                (a) design: Was the failure due to at least one contributing factor introduced by system development, system updates, or procedures to operate or maintain the system?
                                (b) operation: Was the failure due to at least one contributing factor introduced by the operation or misuse of the system?
                                """,
        "boundary":             """
                                (a) within_system: Was the failure due to at least one contributing factor that originates from within the system?
                                (b) outside_system: Was the failure due to at least one contributing factor that originates from outside the system?
                                """,
        "nature":               """
                                (a) non-human_actions: Was the failure due to at least one contributing factor introduced without human participation?
                                (b) human_actions: Was the failure due to at least one contributing factor introduced by human actions?
                                """,
        "dimension":            """
                                (a) hardware: Was the failure due to at least one contributing factor that originates in hardware?
                                (b) software: Was the failure due to at least one contributing factor that originates in software?
                                """,
        "objective":            """
                                (a) malicious: Was the failure due to at least one contributing factor introduced by human(s) with intent to harm the system?
                                (b) non-malicious: Was the failure due to at least one contributing factor introduced without intent to harm the system?
                                """,
        "intent":               """
                                (a) poor_decisions: Was the failure due to at least one contributing factor introduced by poor decisions?
                                (b) accidental_decisions: Was the failure due to at least one contributing factor introduced by mistakes or unintended decisions?
                                """,
        "capability":           """
                                (a) development_incompetence: Was the failure due to at least one contributing factor introduced due to lack of professional competence by humans or development organization?
                                (b) accidental: Was the failure due to at least one contributing factor introduced accidentally?
                                """,
        "duration":             """
                                (a) permanent: Was the failure due to at least one contributing factor introduced by all circumstances?
                                (b) temporary: Was the failure due to at least one contributing factor introduced by certain circumstances but not all?
                                """,
        "behaviour":            """
                                (a) crash: Was the failure due to system losing state and not performing any of its intended functions?
                                (b) omission: Was the failure due to system omitting to perform its intended functions at an instance(s)?
                                (c) timing: Was the failure due to system performing its intended functions correctly, but too late or too early?
                                (d) value: Was the failure due to system performing its intended functions incorrectly?
                                (e) byzantine: Was the failure due to system behaving erroneously with inconsistent responses and interactions?
                                (f) other: Was the failure due to system behaving in a way not described in the other options?
                                """,
        "domain":           ,
        "cps":              ,
        #CPS:
        "perception":       ,
        "communication":    ,
        "application":      ,
}

CPS_KEYS = ["perception","communication","application"]



### DEPRECIATED
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
        "fixes":            "What could fix the software failure incident? (answer in a list)",
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
            "duration": {"0": "permanent", "1": "temporary", "2": "neither", "-1": "unknown"},
            "domain": {"0": "information", "1": "transportation", "2": "natural resources", "3": "sales", "4": "construction", "5": "manufacturing", "6": "utilities", "7": "finance", "8": "knowledge", "9": "health", "10": "entertainment", "11": "government", "12": "consumer device", "13": "multiple", "14": "other", "-1": "unknown"},
            "cps": {"true": "true", "false": "false", "-1": "unknown"},
            "perception": {"0": "sensors", "1": "actuators", "2": "processing unit", "3": "network communication", "4": "embedded software", "-1": "unknown"},
            "communication": {"true": "true", "false": "false", "0": "wired/wireless link level", "1": "connectivity level", "-1": "unknown"},
            "application": {"true": "true", "false": "false", "-1": "unknown"},
            "behaviour": {"0": "crash", "1": "omission", "2": "timing", "3": "incorrect value", "4": "byzantine fault", "-1": "unknown"},
            "recurring": {"true": "true", "false": "false", "0": "within the same impacted entity", "1": "at other entity(s)", "-1": "unknown"},
        }