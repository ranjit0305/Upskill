import re

def _is_valid_technical_question(q_text, found_topic):
    q_low = q_text.lower()
    
    # 0. Strong Structural indicators allow skipping the strict topic requirement
    strong_structural = any(q_low.startswith(start) for start in ["what is", "what are", "difference between", "how does", "what is the difference"])
    
    # 1. Reject if no technical keyword at all AND no strong structural indicator
    if not found_topic and not strong_structural:
        return False
        
    # 2. Broadened blacklist for process/behavioral questions
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

def extract(text):
    patterns = [
        r"(?i)technical question\s*[:]\s*([^.?!,]+?)(?=[.?!, \n]|$)",
        r"(?i)What (is|are) ([^.?!,]+?)\?",
        r"(?i)Difference between ([^.?!,]+?) and ([^.?!,]+?)\?",
        r"(?i)How does ([^.?!,]+?) work\?",
        r"(?i)Explain (?:the concept of |how |what |the implementation of |about )?([^.?!,]{3,100}?)[\.?]",
        r"(?i)Can we ([^.?!,]+?)\?",
        r"(?i)Give (?:a |an |the )?real-life example (?:of |where )([^.?!,]+?)(?:[\.?]|$)",
        r"(?i)What are the (?:types|pillars|features|benefits) of ([^.?!,]+?)\?"
    ]
    
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
    
    questions = []
    for pat in patterns:
        matches = re.finditer(pat, text)
        for m in matches:
            q_text = m.group(0).strip()
            found_topic = False
            for kw in known_keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', q_text, re.IGNORECASE):
                    found_topic = True
                    break
            
            if _is_valid_technical_question(q_text, found_topic):
                questions.append(q_text)
    return questions

sample_text = """
Operating System What is process and thread?
OOPS What are the four pillars of OOPS?
Explain each with example.
What is the difference between abstract class and interface?
Give the real-life example where will you use interface and abstraction?
What are the types of inheritance?
Explain multilevel inheritance with example.
Java Explain try and catch.
Write the code for arithmetic exception.
What is the use of finally?
Explain throw, throws, what is the difference between them?
Can we create object for abstract class?
If I give return statement inside the try method, will the final block be executed
Do you know about Collections, list some of them.
"""

questions = extract(sample_text)
print(f"Extracted {len(questions)} questions:")
for q in questions:
    print(f"- {q}")
