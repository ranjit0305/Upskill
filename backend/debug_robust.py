import re

def _is_valid_technical_question(q_text, found_topic):
    q_low = q_text.lower()
    
    # 0. Strong Structural indicators allow skipping the strict topic requirement
    strong_structural = any(q_low.startswith(start) for start in ["what is", "what are", "difference between", "how does", "what is the difference"])
    
    # 1. Reject if no technical keyword at all AND no strong structural indicator
    if not found_topic and not strong_structural:
        return False
        
    meaningless_indicators = [
        "mentor", "clearly", "how you approached", "discuss", "yourself",
        "round", "interviewer", "manager", "hiring",
        "introduce", "background", "experience", "strength", "weakness",
        "feel", "feedback", "interview", "applied", "joined", "company",
        "preparation", "books", "sites", "resources",
        "before coding", "after coding", "cleared", "selection"
    ]
    if any(ind in q_low for ind in meaningless_indicators):
        return False
        
    technical_triggers = ["what is", "what are", "difference", "how does", "explain", "technical question", "define", "give", "can we", "is it possible"]
    if not any(trigger in q_low for trigger in technical_triggers):
        return False
        
    if any(phrase in q_low for phrase in ["explain it", "explain clearly", "explain your method"]):
        return False
        
    if len(q_text.split()) < 3:
        return False
        
    return True

def extract_robust(text):
    known_keywords = [
        "Java", "Python", "SQL", "DBMS", "OS", "Data Structures", "Algorithms", "Networking", 
        "C++", "React", "Node", "OOPS", "WebRTC", "API", "REST", "Frontend", "Backend", 
        "Fullstack", "DNS", "AWS", "Docker", "Kubernetes", "Microservices", "Security", "Cloud", 
        "Git", "CSS", "HTML", "Javascript", "Typescript", "Thread", "Process", "Deadlock", 
        "Memory", "Cache", "Interface", "Abstract", "Class", "Inheritance", "Polymorphism", 
        "Encapsulation", "Abstraction", "Exception", "Try", "Catch", "Finally", "Throw", 
        "Collection", "List", "Map", "Set", "ArrayList", "LinkedList", "HashMap", "Stack", 
        "Queue", "Recursion", "Complexity", "Big O", "Sorting", "Searching", "Graph", "Tree", 
        "Binary", "Pointer", "Reference", "Constructor", "Destructor", "Static", "Final", 
        "Access Modifier", "Overloading", "Overriding", "Lambda", "Stream", "Async", "Await", 
        "Promise", "Component", "State", "Props", "Hook", "Database", "Index", "Join", "Query", 
        "Transaction", "Normalisation", "Normalization"
    ]

    # 1. Clean the text - join broken lines that look like they belong together
    # In PDFs, tables often extract as separate lines. 
    # But usually, a technical question starts with a trigger word.
    
    # Simple split by newline + basic sentence logic
    lines = text.split('\n')
    current_topic = "General Technical"
    extracted = []
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check if line is a Topic Header (short and in known_keywords)
        if len(line.split()) < 3:
            for kw in known_keywords:
                if kw.lower() == line.lower():
                    current_topic = kw
                    # print(f"DEBUG: Found Category Header: {current_topic}")
                    break
        
        # Check for technical question patterns in the line or part of the line
        # Instead of re.finditer on whole text, we check if the line starts with a trigger or contains a '?'
        
        # Try splitting by '?'
        parts = re.split(r'(\?)', line)
        for i in range(0, len(parts)-1, 2):
            q_candidate = parts[i].strip() + parts[i+1]
            # Heuristic topic detection
            found_topic = False
            q_topic = current_topic
            for kw in known_keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', q_candidate, re.IGNORECASE):
                    q_topic = kw
                    found_topic = True
                    break
            
            if _is_valid_technical_question(q_candidate, found_topic or current_topic != "General Technical"):
                extracted.append((q_candidate, q_topic))
                
        # Also check lines ending with '.' that start with 'Explain' or other triggers
        if not '?' in line:
            if any(line.lower().startswith(t) for t in ["explain", "give", "define", "what is", "can we"]):
                q_candidate = line
                found_topic = False
                q_topic = current_topic
                for kw in known_keywords:
                    if re.search(r'\b' + re.escape(kw) + r'\b', q_candidate, re.IGNORECASE):
                        q_topic = kw
                        found_topic = True
                        break
                
                if _is_valid_technical_question(q_candidate, found_topic or current_topic != "General Technical"):
                    extracted.append((q_candidate, q_topic))

    return extracted

sample_text = """
Operating System
What is process and thread?
OOPS
What are the four pillars of OOPS?
Explain each with example.
What is the difference between abstract class and interface?
Give the real-life example where will you use interface and abstraction?
What are the types of inheritance?
Explain multilevel inheritance with example.
Java
Explain try and catch.
Write the code for arithmetic exception.
What is the use of finally?
Explain throw, throws, what is the difference between them?
Can we create object for abstract class?
If I give return statement inside the try method, will the final block be executed?
Do you know about Collections, list some of them.
"""

questions = extract_robust(sample_text)
print(f"Extracted {len(questions)} questions:")
for q, t in questions:
    print(f"- [{t}] {q}")
