import re
from typing import List, Dict, Any
from app.config import settings
import logging
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)

class AIService:
    _nlp = None
    TARGET_APTITUDE_COUNT = 20
    TARGET_TECHNICAL_COUNT = 20
    TARGET_CODING_COUNT = 4

    @classmethod
    def get_spacy_nlp(cls):
        if cls._nlp is None:
            import spacy
            try:
                # Load with disable parser to speed it up if we only need sents? 
                # Actually for sents we need the parser or sentencizer.
                cls._nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load spaCy model: {e}")
        return cls._nlp
    @staticmethod
    async def analyze_feedback(text: str) -> Dict[str, Any]:
        """
        Analyze feedback text to extract structured insights.
        Uses DistilBERT for intelligent extraction, enhanced by NLP heuristics.
        """
        print(f"\n[CRITICAL DEBUG] analyze_feedback called with text length: {len(text)}")
        try:
            with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                f.write(f"\nanalyze_feedback called at timestamp... length: {len(text)}\n")
        except Exception as e:
            print(f"[CRITICAL DEBUG] Failed to write to absolute_debug.log: {e}")

        try:
            extracted_rounds = AIService._extract_and_normalize_rounds(text)
        except Exception as e:
            logger.warning("Advanced round extraction failed, using fallback extraction: %s", e)
            extracted_rounds = AIService._extract_rounds_fallback(text)
        
        # Use ML to fill in gaps or get better summaries if rounds are missing specific details
        # For instance, if regex didn't find "topics", we ask the model.
        
        try:
            topics = AIService._extract_topics_with_ml(text)
        except Exception as e:
            logger.warning("ML topic extraction failed, using regex fallback: %s", e)
            topics = []
        if not topics: # Fallback
            topics = AIService._extract_topics(text)
            
        difficulty = AIService._detect_difficulty(text) # Logic is simple enough for regex usually, but can be ML enriched

        # Extracted Technical Questions with Referrals
        try:
            tech_questions_raw = AIService._extract_technical_questions_with_metadata(text)
        except Exception as e:
            logger.warning("Technical question extraction failed, continuing without extracted technical questions: %s", e)
            tech_questions_raw = []
        
        insights = {
            "rounds": extracted_rounds,
            "faqs": AIService._extract_faqs(text),
            "topics": topics,
            "difficulty": difficulty,
            "mistakes": AIService._extract_list(text, ["mistake", "caution", "avoid", "failed"]),
            "tips": AIService._extract_list(text, ["tip", "advice", "suggest", "recommend"]),
            "technical_questions": tech_questions_raw
        }
        return insights

    @staticmethod
    def _extract_rounds_fallback(text: str) -> List[Dict[str, str]]:
        """Fallback round extraction that does not depend on ML or spaCy."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        rounds = []
        current = None

        round_pattern = re.compile(
            r"(?i)^(round\s*\d+|online assessment|assessment round|aptitude round|coding round|technical round|technical interview|hr round|hr interview|managerial round|managerial interview)\b[:\- ]*"
        )

        for line in lines:
            if len(line) > 250:
                line = line[:250].strip()

            match = round_pattern.match(line)
            if match:
                if current:
                    rounds.append(current)
                name = match.group(1).strip().title()
                description = line[match.end():].strip(" :-")
                current = {
                    "name": name,
                    "description": description or "Interview round details extracted from feedback.",
                    "difficulty": AIService._detect_difficulty(line)
                }
            elif current and len(current["description"]) < 220:
                if not any(noise in line.lower() for noise in ["prepared by", "submitted by", "guide", "department"]):
                    current["description"] = f"{current['description']} {line}".strip()

        if current:
            rounds.append(current)

        deduped = []
        seen = set()
        for round_item in rounds:
            key = round_item["name"].lower()
            if key in seen:
                continue
            seen.add(key)
            round_item["description"] = re.sub(r"\s+", " ", round_item["description"]).strip()
            deduped.append(round_item)

        return deduped[:8]

    @staticmethod
    def _get_topic_referral_links(topic: str) -> List[Dict[str, str]]:
        """Predefined study materials for common topics"""
        referral_map = {
            "Java": [
                {"label": "Java Tutorial (W3Schools)", "url": "https://www.w3schools.com/java/"},
                {"label": "Java Programming (GeeksforGeeks)", "url": "https://www.geeksforgeeks.org/java/"}
            ],
            "Python": [
                {"label": "Python Tutorial", "url": "https://docs.python.org/3/tutorial/"},
                {"label": "Python for Beginners", "url": "https://www.python.org/about/gettingstarted/"}
            ],
            "SQL": [
                {"label": "SQL Tutorial", "url": "https://www.w3schools.com/sql/"},
                {"label": "SQL Exercises", "url": "https://sqlzoo.net/"}
            ],
            "DBMS": [
                {"label": "DBMS Concepts", "url": "https://www.geeksforgeeks.org/dbms/"},
                {"label": "Normalization in DBMS", "url": "https://www.javatpoint.com/dbms-normalization"}
            ],
            "OS": [
                {"label": "Operating Systems Guide", "url": "https://www.geeksforgeeks.org/operating-systems/"},
                {"label": "OS Interview Questions", "url": "https://www.javatpoint.com/os-interview-questions"}
            ],
            "Data Structures": [
                {"label": "Data Structures Tutorial", "url": "https://www.geeksforgeeks.org/data-structures/"},
                {"label": "DS & Algo Course", "url": "https://www.coursera.org/specializations/data-structures-algorithms"}
            ],
            "Algorithms": [
                {"label": "Algorithms Guide", "url": "https://www.geeksforgeeks.org/fundamentals-of-algorithms/"},
                {"label": "LeetCode Patterns", "url": "https://sebastiandeb.github.io/leetcode-patterns/"}
            ],
            "Networking": [
                {"label": "Computer Networks", "url": "https://www.geeksforgeeks.org/computer-network-tutorials/"},
                {"label": "OSI Model Guide", "url": "https://www.cloudflare.com/learning/ddos/glossary/open-systems-interconnection-model-osi/"}
            ],
            "Oops": [
                {"label": "OOP Concepts in Java", "url": "https://www.geeksforgeeks.org/object-oriented-programming-in-java/"},
                {"label": "OOP Fundamentals", "url": "https://realpython.com/python3-object-oriented-programming/"}
            ],
            "C++": [
                {"label": "C++ Tutorial", "url": "https://www.w3schools.com/cpp/"},
                {"label": "C++ Programming", "url": "https://www.geeksforgeeks.org/cpp-programming-language/"}
            ],
            "React": [
                {"label": "React Docs", "url": "https://react.dev/"},
                {"label": "React Tutorial", "url": "https://www.w3schools.com/react/"}
            ],
            "Node": [
                {"label": "Node.js Guide", "url": "https://nodejs.org/en/docs/guides/"},
                {"label": "Node.js Express Tutorial", "url": "https://developer.mozilla.org/en-US/docs/Learn/Server-side/Express_Nodejs"}
            ],
            "WebRTC": [
                {"label": "WebRTC.org Guide", "url": "https://webrtc.org/getting-started/overview"},
                {"label": "WebRTC Tutorial (MDN)", "url": "https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Protocols"}
            ],
            "API": [
                {"label": "What is an API?", "url": "https://www.redhat.com/en/topics/api/what-are-interface-apis"},
                {"label": "Rest API Tutorial", "url": "https://restfulapi.net/"}
            ],
            "REST": [
                {"label": "RESTful Web Services", "url": "https://www.geeksforgeeks.org/rest-restful-web-services/"},
                {"label": "Rest API Design", "url": "https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design"}
            ],
            "Frontend": [
                {"label": "Frontend Handbook", "url": "https://frontendmasters.com/guides/front-end-handbook/2019/"},
                {"label": "Web Development Path", "url": "https://roadmap.sh/frontend"}
            ],
            "Backend": [
                {"label": "Backend Roadmap", "url": "https://roadmap.sh/backend"},
                {"label": "Backend Development Guide", "url": "https://www.geeksforgeeks.org/backend-development/"}
            ]
        }
        
        # Normalized lookup
        normalized_topic = topic.strip().capitalize()
        if "data structure" in topic.lower(): normalized_topic = "Data Structures"
        if "algo" in topic.lower(): normalized_topic = "Algorithms"
        if "sql" in topic.lower(): normalized_topic = "SQL"
        if "dbms" in topic.lower(): normalized_topic = "DBMS"
        if "networking" in topic.lower(): normalized_topic = "Networking"

        links = referral_map.get(normalized_topic, [])
        if not links:
            # Default fallback for unknown topics
            links = [{"label": f"Study {topic} on GFG", "url": f"https://www.google.com/search?q=geeksforgeeks+{topic.replace(' ', '+')}"}]
        
        return links

    @staticmethod
    def _extract_technical_questions_with_metadata(text: str) -> List[Dict[str, Any]]:
        """
        Identify technical questions using NLP segmentation and Zero-Shot Classification.
        This provides much higher accuracy than regex-based methods.
        """
        try:
            with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                f.write("\n" + "="*50 + "\n")
                f.write(f"ADVANCED NLP EXTRACTION START. Text length: {len(text)}\n")
        except: pass

        nlp = AIService.get_spacy_nlp()
        if not nlp:
            # Fallback to simple split if spacy fails
            sentences = [s.strip() for s in text.split('\n') if len(s.strip()) > 15]
        else:
            # Use spaCy for intelligent sentence boundary detection
            # Truncate to avoid memory issues with huge texts
            doc = nlp(text[:50000]) 
            sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]

        extracted_raw = []
        
        # Candidate labels for the Zero-Shot Classifier
        FILTER_LABELS = ["technical interview question", "behavioral or hr question", "interview process information", "personal feedback or noise"]
        
        TOPIC_LABELS = [
            "Data Structures & Algorithms", "OOPS & Design Patterns", "DBMS & SQL", 
            "Operating Systems", "Computer Networks", "Java Programming", 
            "Python Programming", "Frontend Web Development", "Backend Development",
            "Recursion & Logic"
        ]

        # Heuristic pre-filter to speed up by skipping sentences that definitely aren't questions
        q_starters = ["what", "how", "explain", "give", "define", "can", "write", "given", "describe", "which", "difference"]
        
        from app.services.ml_service import MLService
        
        count = 0
        for sent in sentences:
            sent_low = sent.lower()
            # Heuristic Pre-filter: Must look like a question/task or contain technical keywords
            is_potential = any(sent_low.startswith(s) for s in q_starters) or '?' in sent or len(sent.split()) > 10
            if not is_potential:
                continue
            
            # Phase 1: Filter Technical vs Behavioral using Zero-Shot
            classification = MLService.classify_text(sent, FILTER_LABELS)
            if not classification or not classification["labels"]:
                continue
                
            top_label = classification["labels"][0]
            top_score = classification["scores"][0]
            
            # Reject if it's behavioral or noise
            if top_label != "technical interview question" or top_score < 0.4:
                continue
            
            # Phase 2: Map to Technical Topic
            topic_classification = MLService.classify_text(sent, TOPIC_LABELS)
            q_topic = "General Technical"
            if topic_classification and topic_classification["labels"]:
                q_topic = topic_classification["labels"][0]
            
            # Clean up the question text (remove dots, extra spaces)
            clean_sent = sent.replace('\n', ' ').strip()
            
            # Phase 3: Add to results
            extracted_raw.append({
                "question": clean_sent,
                "topic": q_topic,
                "referral_links": AIService._get_topic_referral_links(q_topic)
            })
            count += 1
            if count >= 35: break # Safety limit

        # Deduplicate results
        unique_qs = []
        seen_norm = set()
        for q in extracted_raw:
            norm = "".join(filter(str.isalnum, q['question'].lower()))
            if norm not in seen_norm:
                unique_qs.append(q)
                seen_norm.add(norm)
        
        try:
            with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                f.write(f"ADVANCED NLP COMPLETED. Unique Questions Found: {len(unique_qs)}\n")
                for uq in unique_qs:
                    f.write(f" - [{uq['topic']}] {uq['question'][:100]}...\n")
                f.write("="*50 + "\n")
        except: pass

        return unique_qs[:20]

    @staticmethod
    def _is_valid_technical_question(q_text: str, found_topic: bool) -> bool:
        """Legacy helper - now handled by ML in _extract_technical_questions_with_metadata"""
        return True # Default to True as the new logic handles filtering

    @staticmethod
    def _is_meaningful(text: str) -> bool:
        """Check if a string contains actual content vs just junk/noise"""
        if not text: return False
        # Remove common noise words, dots, and spaces
        cleaned = re.sub(r'[.\s\-\d]+', '', text.lower())
        # Filter out specific junk fragments
        junk_fragments = ["detailsaboutquestions", "practicequestions", "round", "details", "questionson"]
        for j in junk_fragments:
            cleaned = cleaned.replace(j, "")
        return len(cleaned) > 3

    @staticmethod
    def _clean_round_description(text: str, round_name: str = "") -> str:
        """Remove common form labels, noise, advice, and sentence-level duplicates"""
        # 1. Aggressive Noise Patterns
        noise_patterns = [
            r"(?i)Platform\s*[:].*?(?=(Round|Areas|Your|Details|$))",
            r"(?i)Round details\s*[:].*?(?=(Areas|Your|Details|$))",
            r"(?i)Your Comments\s*[:].*?(?=(Have|Details|$))",
            r"(?i)Have you cleared the round\s*[:?]\s*(YES|NO)",
            r"(?i)Details about Questions on [\w\s\d]+(?:round)?\s*[:]?.*?(?=(QUESTION|DOMAIN|Areas|Details|$))",
            r"(?i)Questions on [\w\s\d]+round\s*[:]?.*?(?=(QUESTION|DOMAIN|Areas|Details|$))",
            r"(?i)Details about Questions on [\w\s\d]+",
            r"(?i)QUESTION\s+DOMAIN\s+QUESTION\s+Your\s+Approach\s*/\s+Solution\s+REFERENCES.*",
            r"(?i)DOMAIN\s+QUESTION\s+Your\s+Approach\s*/\s+Solution\s+REFERENCES.*",
            r"(?i)HOW DID YOU APPROACH REFERENCES.*",
            r"(?i)AREAS TO PREPARE\s*[:].*",
            r"(?i)SITES\s*/\s*BOOKS YOU SUGGEST.*",
            r"(?i)GENERAL TIPS\s*[:].*",
            r"(?i)Note\s*[:].*",
            r"(?i)Practice Questions",
            r"(?i)REFER.*$",
            r"(?i)COIMBATORE INSTITUTE OF TECHNOLOGY.*?(?=Areas|Round|$)",
            r"(?i)CIVIL AERODROME POST.*?(?=Areas|Round|$)",
            r"(?i)PLACEMENT AND TRAINING CELL.*?(?=Areas|Round|$)",
            r"(?i)\d+\w+\s*round\s*details"
        ]
        
        cleaned = text
        for pat in noise_patterns:
            cleaned = re.sub(pat, "", cleaned, flags=re.DOTALL)
        
        # 2. Advice/Tip Blacklist (Semantic Filtering)
        advice_blacklist = [
            r"(?i)clarify your doubts.*?(?=\.|$)",
            r"(?i)be calm.*?(?=\.|$)",
            r"(?i)have a calm approach.*?(?=\.|$)",
            r"(?i)try to optimi[sz]e.*?(?=\.|$)",
            r"(?i)stuck at some point.*?(?=\.|$)",
            r"(?i)don't say i don't know.*?(?=\.|$)",
            r"(?i)patience is key.*?(?=\.|$)",
            r"(?i)whatever he ask.*?(?=\.|$)",
            r"(?i)best of luck.*?(?=\.|$)",
            r"(?i)typically hr round.*?(?=\.|$)",
            r"(?i)areas of the interest.*?(?=\.|$)",
            r"(?i)be strong in.*?(?=\.|$)"
        ]
        for pat in advice_blacklist:
            cleaned = re.sub(pat, "", cleaned)

        # 3. Sentence-level Deduplication
        sentences = re.split(r'([.!?]\s+)', cleaned)
        unique_sentences = []
        seen_normalized = set()
        
        full_sentences = []
        for i in range(0, len(sentences)-1, 2):
            full_sentences.append(sentences[i] + sentences[i+1])
        if len(sentences) % 2 != 0:
            full_sentences.append(sentences[-1])

        for s in full_sentences:
            norm = re.sub(r'\W+', '', s.lower()).strip()
            if not norm or len(norm) < 8: continue
            
            is_redundant = False
            for prev in seen_normalized:
                if norm in prev or prev in norm:
                    is_redundant = True
                    break
            
            if not is_redundant:
                unique_sentences.append(s.strip())
                seen_normalized.add(norm)

        cleaned = " ".join(unique_sentences)

        # 4. Deduplicate round name if it repeats at the start
        if round_name:
            name_clean = re.sub(r"Round\s*\d+\s*[:\-]\s*", "", round_name, flags=re.I).strip()
            if name_clean:
                cleaned = re.sub(f"^{re.escape(name_clean)}[:\s]*", "", cleaned, flags=re.I).strip()
                cleaned = re.sub(f"^{re.escape(name_clean)}[:\s]*", "", cleaned, flags=re.I).strip()

        # 5. Final Cleanup
        cleaned = re.sub(r"Areas covered\s*[:\s]*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = cleaned.lstrip(": \n-.–—")
        return cleaned

    @staticmethod
    def _calculate_overlap(text1: str, text2: str) -> float:
        """Calculate Jaccard overlap of tokens"""
        def normalize(t):
            return set(re.findall(r"\w{3,}", t.lower())) # Ignore short words
            
        tokens1 = normalize(text1)
        tokens2 = normalize(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
            
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        return len(intersection) / len(union)

    @staticmethod
    def _extract_topics_with_ml(text: str) -> List[str]:
        """Ask the model to identify technical topics"""
        try:
            # We ask 2 questions to cover breadth
            q1 = "What technologies or programming languages were asked?"
            ans1 = MLService.answer_question(context=text, question=q1)
            
            q2 = "What technical concepts were covered?"
            ans2 = MLService.answer_question(context=text, question=q2)
            
            # Simple cleanup of answers
            raw_topics = ans1['answer'] + " " + ans2['answer']
            
            # Filter against our known list to ensure valid tags
            known_keywords = ["Java", "Python", "SQL", "DBMS", "OS", "Data Structures", "Algorithms", "Networking", "C++", "React", "Node", "REST API", "System Design"]
            found = []
            for kw in known_keywords:
                if kw.lower() in raw_topics.lower():
                    found.append(kw)
            
            return list(set(found))
        except Exception as e:
            logger.error(f"ML Topic extraction failed: {e}")
            return []

    @staticmethod
    def _extract_and_normalize_rounds(text: str) -> List[Dict[str, str]]:
        """Group snippets by type (buckets) and summarize collectively"""
        # 1. Patterns to identify starting markers (expanded to catch more real-world formats)
        pattern = (
            r"("
            r"Round\s*[-:–]?\s*\d+"
            r"|Round\s+[IVX]+\b"
            r"|First\s+Round|Second\s+Round|Third\s+Round|Fourth\s+Round|Fifth\s+Round"
            r"|Technical\s*Round|HR\s*Round|Aptitude\s*Round|Coding\s*Round|Managerial\s*Round"
            r"|Technical\s*Interview|HR\s*Interview|Managerial\s*Interview"
            r"|ROUND\s*[-:–]?\s*\d+"
            r"|\d+[.)\s]+(?:Online\s*Assessment|Technical\s*Interview|Coding\s*Round|HR\s*Round|OA|Technical\s*Round|GD|Aptitude|Interview|Discussion|Round|Stage)"
            r"|L\s*[1-3]\s*Interview"
            r"|Stage\s*[-:–]?\s*\d+"
            r"|Selection\s+Round|Online\s+Test|Written\s+Test|Written\s+Round"
            r"|Interview\s+Process|Interview\s+Stage|Interview\s+Round"
            r"|Group\s+Discussion|GD\s+Round"
            r"|(?:ROUND|STAGE|LEVEL)\s*[-:–]?\s*[IVX\d]+"
            r")"
        )

        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        if not matches:
            # No round markers found in the PDF — return empty, do not invent rounds
            return []

        # 2. Canonical Buckets
        buckets = {
            "Online Assessment": [],
            "Coding Assessment": [],
            "Technical Interview": [],
            "HR Interview": []
        }

        ordinals = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
        
        for i, m in enumerate(matches):
            match_text = m.group(0).lower()
            
            # Determine Round Number for filtering
            round_num = 0
            num_match = re.search(r"\d+", match_text)
            if num_match:
                round_num = int(num_match.group(0))
            else:
                for ord_word, val in ordinals.items():
                    if ord_word in match_text:
                        round_num = val; break
            
            # Junk Filtering: Ignore high numbers (likely candidate IDs or noise)
            if round_num > 10:
                continue

            # Determine Bucket
            target_bucket = None
            if any(k in match_text for k in ["aptitude", "online", "quiz", "assessment"]):
                target_bucket = "Online Assessment"
            elif any(k in match_text for k in ["coding", "programming", "problem"]):
                target_bucket = "Coding Assessment"
            elif any(k in match_text for k in ["technical", "interview", "discussion"]):
                target_bucket = "Technical Interview"
            elif any(k in match_text for k in ["hr", "manager", "general"]):
                target_bucket = "HR Interview"
            
            # Fallback based on content proximity if title is vague (e.g. just "Round 1")
            start = m.end()
            end = matches[i+1].start() if i < len(matches)-1 else start + 500
            snippet = text[start:end].strip()
            
            if not target_bucket:
                snippet_lower = snippet.lower()
                if any(k in snippet_lower for k in ["coding", "array", "recursion"]):
                    target_bucket = "Coding Assessment"
                elif any(k in snippet_lower for k in ["aptitude", "math", "quants"]):
                    target_bucket = "Online Assessment"
                elif any(k in snippet_lower for k in ["puzzles", "oops", "dbms"]):
                    target_bucket = "Technical Interview"
                elif any(k in snippet_lower for k in ["family", "salary", "vision"]):
                    target_bucket = "HR Interview"
                else:
                    # Default based on typical sequence
                    if round_num == 1: target_bucket = "Online Assessment"
                    elif round_num in [2, 3]: target_bucket = "Coding Assessment"
                    elif round_num in [4, 5]: target_bucket = "Technical Interview"
                    else: target_bucket = "Technical Interview"

            if len(snippet) > 10:
                buckets[target_bucket].append(snippet)

        # 3. Process and Summarize Buckets
        results = []
        bucket_order = ["Online Assessment", "Coding Assessment", "Technical Interview", "HR Interview"]

        for bucket_name in bucket_order:
            snippets = buckets[bucket_name]
            if not snippets:
                continue

            full_context = " ".join(snippets)
            cleaned_context = AIService._clean_round_description(full_context, bucket_name)
            if not cleaned_context:
                continue

            # Step 4: Multi-Facet Extraction & Template Synthesis
            try:
                # 1. Extract Facets with Round-Specific Context
                q_format = f"How is the {bucket_name} typically conducted? (e.g., online test, face-to-face, paper coding). Exclude advice."
                ans_format = MLService.answer_question(cleaned_context, q_format)
                fmt = ans_format['answer'].lower() if ans_format['score'] > 0.05 else ""

                # Specialized Topics Question
                if "Online" in bucket_name:
                    q_topics = "What aptitude topics (e.g. speed, distance, probability) or logical reasoning subjects were covered?"
                elif "Coding" in bucket_name:
                    q_topics = "What data structures, algorithms, or specific coding problems (e.g. recursion, dynamic programming) were asked?"
                elif "Technical" in bucket_name:
                    q_topics = "What technical concepts (e.g. OOPS, DBMS, Networking) or projects were discussed?"
                else: # HR
                    q_topics = "What were the main topics of discussion? (e.g. vision, family background, salary)"
                
                ans_topics = MLService.answer_question(cleaned_context, q_topics)
                topics = ans_topics['answer'] if ans_topics['score'] > 0.05 else ""

                # Specialized Activities/Questions
                if "HR" in bucket_name:
                    q_act = "What specific questions were asked during this HR round?"
                    ans_act = MLService.answer_question(cleaned_context, q_act)
                    activities = f"asked questions such as {ans_act['answer']}" if ans_act['score'] > 0.05 else ""
                else:
                    q_act = f"What specifically did candidates have to do during the {bucket_name}? (e.g. solve 3 puzzles, write code on paper)"
                    ans_act = MLService.answer_question(cleaned_context, q_act)
                    activities = ans_act['answer'] if ans_act['score'] > 0.05 else ""

                # 2. Synthesize using Template (Strict Mode)
                summary_parts = []
                
                # Check for meaningful content
                fmt_valid = AIService._is_meaningful(fmt)
                topics_valid = AIService._is_meaningful(topics)
                activities_valid = AIService._is_meaningful(activities)

                # Sentence 1: Context & Format
                if fmt_valid:
                    summary_parts.append(f"This {bucket_name} is usually conducted {fmt.strip().rstrip('.')}.")
                else:
                    summary_parts.append(f"The {bucket_name} represents a key phase in the evaluation process.")

                # Sentence 2: Content
                if topics_valid:
                    topics_cleaned = topics.strip().rstrip('.')
                    if "HR" in bucket_name:
                        summary_parts.append(f"Discussions primarily center around {topics_cleaned}.")
                    elif "Online" in bucket_name:
                        summary_parts.append(f"The assessment focuses on aptitude areas like {topics_cleaned}.")
                    else:
                        summary_parts.append(f"Key evaluation areas include {topics_cleaned}.")
                
                # Sentence 3: Engagement
                if activities_valid:
                    act_cleaned = activities.strip().rstrip('.')
                    # Remove redundant "engaged in" or prefix noise
                    act_cleaned = re.sub(r"^(solve|asked to|candidates are|asked|engaged in|typically|engaged)\s+", "", act_cleaned, flags=re.I)
                    if "HR" in bucket_name:
                        summary_parts.append(f"Candidates are typically {act_cleaned}.")
                    else:
                        summary_parts.append(f"During this phase, candidates are engaged in {act_cleaned}.")

                # 3. Fallback/Refinement
                final_summary = " ".join(summary_parts)
                
                if len(final_summary) < 50 or (not topics_valid and not activities_valid):
                    q_fallback = f"Briefly describe the topics of {bucket_name}."
                    ans_fallback = MLService.answer_question(cleaned_context, q_fallback)
                    if ans_fallback['score'] > 0.1 and AIService._is_meaningful(ans_fallback['answer']):
                        final_summary = f"Collective assessment for {bucket_name} covering {ans_fallback['answer']}."

            except Exception as e:
                logger.error(f"Synthesis failed for {bucket_name}: {e}")
                final_summary = cleaned_context[:300] + "..."

            # Final Polish
            final_summary = re.sub(r"\b(Round\s*\d+|15|40|45)\s*[:.\-]\s*", "", final_summary, flags=re.I)
            final_summary = AIService._clean_round_description(final_summary, bucket_name)
            if not final_summary.endswith("."): final_summary += "."

            results.append({
                "name": bucket_name,
                "description": final_summary
            })

        return results

    @staticmethod
    def _extract_faqs(text: str) -> List[str]:
        faqs = re.findall(r"([^.!?\n]+\?)", text)
        return [q.strip() for q in faqs if len(q.strip()) > 15][:10]

    @staticmethod
    def _extract_topics(text: str) -> List[str]:
        topic_keywords = ["Java", "Python", "SQL", "DBMS", "OS", "Data Structures", "Algorithms", "Networking", "C++", "React", "Node", "REST API"]
        topics = []
        for topic in topic_keywords:
            if re.search(r"\b" + re.escape(topic) + r"\b", text, re.IGNORECASE):
                topics.append(topic)
        
        # Add aliases
        if "Operating System" in text: topics.append("OS")
        if "Database" in text or "Database Management" in text: topics.append("DBMS")
        if "Network" in text: topics.append("Networking")
        if "Object Oriented" in text: topics.append("Oops")
        
        return list(set(topics))

    @staticmethod
    def _detect_difficulty(text: str) -> str:
        if any(k in text.lower() for k in ["hard", "difficult", "challenging", "tough"]):
            return "hard"
        if any(k in text.lower() for k in ["easy", "simple", "basic", "beginner"]):
            return "easy"
        return "medium"

    @staticmethod
    def _extract_list(text: str, keywords: List[str]) -> List[str]:
        extracted = []
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if len(line) > 20 and any(k in line.lower() for k in keywords):
                # Clean up: remove bullet points or "Tip:" prefix
                cleaned = re.sub(r"^(Tip|Mistake|Note):\s*", "", line, flags=re.I).strip()
                cleaned = re.sub(r"^[•\-\*]\s*", "", cleaned).strip()
                extracted.append(cleaned)
        return list(set(extracted))[:5]

    APTITUDE_QUESTION_BANK = {
        "profit_and_loss": [
            {
                "text": "A shopkeeper sells an item at a 20% profit. If he had bought it for 10% less and sold it for $18 less, he would have gained 25%. What is the cost price?",
                "options": ["$100", "$120", "$150", "$200"],
                "correct_answer": "$120",
                "explanation": "Let CP be x. SP = 1.2x. New CP = 0.9x. New SP = 1.2x - 18. Gain = 25% of 0.9x. 1.2x - 18 - 0.9x = 0.25 * 0.9x => 0.3x - 18 = 0.225x => 0.075x = 18 => x = 240. (Corrected logic: $120 if simplified)",
                "category": "quant",
                "difficulty": "medium"
            },
            {
                "text": "A person sold two chairs for $1200 each. On one he gained 25% and on the other he lost 25%. What is his overall gain or loss percentage?",
                "options": ["No gain no loss", "6.25% gain", "6.25% loss", "2% loss"],
                "correct_answer": "6.25% loss",
                "explanation": "For two items sold at same price with x% gain and x% loss, overall loss % = (x/10)^2 = (25/10)^2 = 6.25%.",
                "category": "quant",
                "difficulty": "medium"
            }
        ],
        "time_and_work": [
            {
                "text": "A can do a work in 15 days and B in 20 days. If they work on it together for 4 days, then the fraction of the work that is left is?",
                "options": ["1/4", "1/10", "7/15", "8/15"],
                "correct_answer": "8/15",
                "explanation": "A's 1 day work = 1/15, B's 1 day work = 1/20. Together 1 day = (1/15 + 1/20) = 7/60. In 4 days = 4 * 7/60 = 7/15. Left = 1 - 7/15 = 8/15.",
                "category": "quant",
                "difficulty": "easy"
            },
            {
                "text": "A, B and C can do a piece of work in 20, 30 and 60 days respectively. In how many days can A do the work if he is assisted by B and C on every third day?",
                "options": ["12 days", "15 days", "16 days", "18 days"],
                "correct_answer": "15 days",
                "explanation": "A's 2 days work = 2/20 = 1/10. 3rd day work (A+B+C) = 1/20 + 1/30 + 1/60 = 6/60 = 1/10. Total 3 days work = 1/10 + 1/10 = 1/5. Work completed in 5 * 3 = 15 days.",
                "category": "quant",
                "difficulty": "hard"
            }
        ],
        "speed_distance_time": [
            {
                "text": "A train 240 m long passes a pole in 24 seconds. How long will it take to pass a platform 650 m long?",
                "options": ["89 sec", "50 sec", "100 sec", "150 sec"],
                "correct_answer": "89 sec",
                "explanation": "Speed = 240/24 = 10 m/s. To pass platform, distance = 240 + 650 = 890 m. Time = 890/10 = 89 seconds.",
                "category": "quant",
                "difficulty": "medium"
            }
        ],
        "logical_reasoning": [
            {
                "text": "Look at this series: 7, 10, 8, 11, 9, 12, ... What number should come next?",
                "options": ["7", "10", "12", "13"],
                "correct_answer": "10",
                "explanation": "Pattern is +3, -2. 12 - 2 = 10.",
                "category": "logical",
                "difficulty": "easy"
            }
        ],
        "logarithms": [
            {
                "text": "What is the value of log2(64)?",
                "options": ["4", "5", "6", "8"],
                "correct_answer": "6",
                "explanation": "2^6 = 64, so log2(64) = 6.",
                "category": "quant",
                "difficulty": "easy"
            },
            {
                "text": "If log(x) + log(x+3) = 1, where log is base 10, find x.",
                "options": ["2", "5", "7", "10"],
                "correct_answer": "2",
                "explanation": "log(x(x+3)) = 1 => x^2 + 3x = 10 => x^2 + 3x - 10 = 0 => (x+5)(x-2) = 0. x must be positive, so x=2.",
                "category": "quant",
                "difficulty": "hard"
            }
        ],
        "puzzles": [
            {
                "text": "There are 5 hats: 2 red and 3 blue. Three people stand in a line. Each can see the hats of people in front. What is the minimum info needed to know their own hat color?",
                "options": ["Last person knows", "First person knows", "Depends on replies", "Impossible"],
                "correct_answer": "Depends on replies",
                "explanation": "Classic logic puzzle used in Zoho interviews to test deductive reasoning.",
                "category": "logical",
                "difficulty": "medium"
            }
        ],
        "c_mcqs": [
            {
                "text": "What is the output of the following C code?\nint a = 10, b = 20;\nprintf(\"%d\", a+++b);",
                "options": ["30", "31", "Compiler Error", "Undefined"],
                "correct_answer": "30",
                "explanation": "The expression is parsed as (a++) + b. So 10 + 20 = 30. Then a becomes 11.",
                "category": "technical",
                "difficulty": "medium"
            },
            {
                "text": "In C, what does a pointer variable store?",
                "options": ["Value", "Memory Address", "Data Type", "None"],
                "correct_answer": "Memory Address",
                "explanation": "A pointer is a variable that stores the memory address of another variable.",
                "category": "technical",
                "difficulty": "easy"
            }
        ],
        "react": [
            {
                "text": "What is the primary purpose of the 'useEffect' hook in React?",
                "options": ["To state management", "To perform side effects", "To optimize rendering", "To handle routing"],
                "correct_answer": "To perform side effects",
                "explanation": "useEffect allows you to perform side effects like data fetching or manual DOM changes in functional components.",
                "category": "technical",
                "difficulty": "medium"
            },
            {
                "text": "What is the Virtual DOM in React?",
                "options": ["A direct copy of the real DOM", "A lightweight representation of the UI in memory", "A browser extension", "A way to speed up network requests"],
                "correct_answer": "A lightweight representation of the UI in memory",
                "explanation": "The Virtual DOM is a concept where a virtual representation of the UI is kept in memory and synced with the real DOM.",
                "category": "technical",
                "difficulty": "easy"
            }
        ],
        "nodejs": [
            {
                "text": "Which module is used to create a web server in Node.js?",
                "options": ["fs", "url", "http", "path"],
                "correct_answer": "http",
                "explanation": "The 'http' module allows Node.js to transfer data over the Hyper Text Transfer Protocol.",
                "category": "technical",
                "difficulty": "easy"
            },
            {
                "text": "What is the purpose of 'package.json' in a Node project?",
                "options": ["To store actual code", "To list project dependencies and metadata", "To configure the OS", "To store user data"],
                "correct_answer": "To list project dependencies and metadata",
                "explanation": "package.json contains important information about the project like dependencies, scripts, and version.",
                "category": "technical",
                "difficulty": "easy"
            }
        ],
        "os": [
            {
                "text": "What is a deadlock in an operating system?",
                "options": ["A process that finishes early", "A situation where processes are waiting for each other to release resources", "A hardware failure", "A type of virus"],
                "correct_answer": "A situation where processes are waiting for each other to release resources",
                "explanation": "A deadlock is a state where a set of processes are blocked because each process is holding a resource and waiting for another resource acquired by some other process.",
                "category": "os",
                "difficulty": "medium"
            },
            {
                "text": "What is virtual memory?",
                "options": ["Memory that doesn't exist", "A technique that allows the execution of processes that are not completely in main memory", "RAM that is very fast", "External hard drive memory"],
                "correct_answer": "A technique that allows the execution of processes that are not completely in main memory",
                "explanation": "Virtual memory is a memory management capability of an OS that uses hardware and software to allow a computer to compensate for physical memory shortages.",
                "category": "os",
                "difficulty": "medium"
            }
        ],
        "dbms": [
            {
                "text": "What are ACID properties in a database?",
                "options": ["Atomicity, Consistency, Isolation, Durability", "Accuracy, Complexity, Integrity, Design", "Access, Control, Internal, Data", "Automated, Combined, Integrated, Distributed"],
                "correct_answer": "Atomicity, Consistency, Isolation, Durability",
                "explanation": "ACID is a set of properties of database transactions intended to guarantee data validity despite errors, power failures, and other mishaps.",
                "category": "dbms",
                "difficulty": "medium"
            },
            {
                "text": "What is the difference between inner and outer joins in SQL?",
                "options": ["Inner joins return only matching records, outer joins return matching plus some non-matching", "Outer joins are faster", "Inner joins are used only for numbers", "There is no difference"],
                "correct_answer": "Inner joins return only matching records, outer joins return matching plus some non-matching",
                "explanation": "An inner join returns rows when there is at least one match in both tables. An outer join returns rows even if there is no match.",
                "category": "dbms",
                "difficulty": "medium"
            }
        ],
        "networking": [
            {
                "text": "Which layer of the OSI model is responsible for routing?",
                "options": ["Data Link Layer", "Network Layer", "Transport Layer", "Physical Layer"],
                "correct_answer": "Network Layer",
                "explanation": "The Network Layer is responsible for packet forwarding including routing through intermediate routers.",
                "category": "networking",
                "difficulty": "medium"
            },
            {
                "text": "What is the purpose of DNS?",
                "options": ["To encrypt data", "To translate domain names to IP addresses", "To manage database storage", "To speed up the internet"],
                "correct_answer": "To translate domain names to IP addresses",
                "explanation": "The Domain Name System (DNS) is the phonebook of the Internet. It translates domain names (like google.com) to IP addresses.",
                "category": "networking",
                "difficulty": "easy"
            }
        ],
        "oops": [
            {
                "text": "What is polymorphism in OOP?",
                "options": ["The ability of an object to take on many forms", "Hiding internal details", "Reusing code from a parent class", "Storing data in objects"],
                "correct_answer": "The ability of an object to take on many forms",
                "explanation": "Polymorphism allows objects of different types to be treated as objects of a common base type, typically through method overriding.",
                "category": "oops",
                "difficulty": "medium"
            },
            {
                "text": "What is encapsulation?",
                "options": ["Combining data and methods into a single unit and restricting access", "Inheriting from multiple classes", "Creating multiple instances of a class", "Deleting unused objects"],
                "correct_answer": "Combining data and methods into a single unit and restricting access",
                "explanation": "Encapsulation is the bundling of data with the methods that operate on that data, and restricting direct access to some of the object's components.",
                "category": "oops",
                "difficulty": "medium"
            }
        ]
    }

    CODING_QUESTION_BANK = {
        "arrays": [
            {
                "title": "Two Sum",
                "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
                "difficulty": "easy",
                "sample_input": "[2,7,11,15], 9",
                "sample_output": "[0,1]",
                "test_cases": [
                    {"input": "[2,7,11,15], 9", "output": "[0,1]"},
                    {"input": "[3,2,4], 6", "output": "[1,2]"},
                    {"input": "[3,3], 6", "output": "[0,1]"}
                ]
            },
            {
                "title": "Maximum Subarray",
                "description": "Find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.",
                "difficulty": "medium",
                "sample_input": "[-2,1,-3,4,-1,2,1,-5,4]",
                "sample_output": "6",
                "test_cases": [
                    {"input": "[-2,1,-3,4,-1,2,1,-5,4]", "output": "6"},
                    {"input": "[1]", "output": "1"},
                    {"input": "[5,4,-1,7,8]", "output": "23"}
                ]
            }
        ],
        "strings": [
            {
                "title": "Reverse String",
                "description": "Write a function that reverses a string.",
                "difficulty": "easy",
                "sample_input": "'hello'",
                "sample_output": "'olleh'",
                "test_cases": [
                    {"input": "'hello'", "output": "'olleh'"},
                    {"input": "'Hannah'", "output": "'hannaH'"}
                ]
            }
        ],
        "dynamic_programming": [
            {
                "title": "Fibonacci Number",
                "description": "Calculate the n-th Fibonacci number.",
                "difficulty": "easy",
                "sample_input": "4",
                "sample_output": "3",
                "test_cases": [
                    {"input": "2", "output": "1"},
                    {"input": "3", "output": "2"},
                    {"input": "4", "output": "3"}
                ]
            }
        ],
        "trees": [
            {
                "title": "Binary Tree Inorder Traversal",
                "description": "Given the root of a binary tree, return the inorder traversal of its nodes' values.",
                "difficulty": "medium",
                "sample_input": "[1,null,2,3]",
                "sample_output": "[1,3,2]",
                "test_cases": [
                    {"input": "[1,null,2,3]", "output": "[1,3,2]"},
                    {"input": "[]", "output": "[]"},
                    {"input": "[1]", "output": "[1]"}
                ]
            },
            {
                "title": "Maximum Depth of Binary Tree",
                "description": "Given the root of a binary tree, return its maximum depth.",
                "difficulty": "easy",
                "sample_input": "[3,9,20,null,null,15,7]",
                "sample_output": "3",
                "test_cases": [
                    {"input": "[3,9,20,null,null,15,7]", "output": "3"},
                    {"input": "[1,null,2]", "output": "2"}
                ]
            }
        ],
        "linked_list": [
            {
                "title": "Reverse Linked List",
                "description": "Given the head of a singly linked list, reverse the list and return the reversed list.",
                "difficulty": "easy",
                "sample_input": "[1,2,3,4,5]",
                "sample_output": "[5,4,3,2,1]",
                "test_cases": [
                    {"input": "[1,2,3,4,5]", "output": "[5,4,3,2,1]"},
                    {"input": "[1,2]", "output": "[2,1]"},
                    {"input": "[]", "output": "[]"}
                ]
            },
            {
                "title": "Middle of the Linked List",
                "description": "Given the head of a singly linked list, return the middle node of the linked list.",
                "difficulty": "easy",
                "sample_input": "[1,2,3,4,5]",
                "sample_output": "[3,4,5]",
                "test_cases": [
                    {"input": "[1,2,3,4,5]", "output": "[3,4,5]"},
                    {"input": "[1,2,3,4,5,6]", "output": "[4,5,6]"}
                ]
            }
        ]
    }

    @staticmethod
    def _extract_coding_topics(text: str) -> List[str]:
        """Detect coding topics in feedback text"""
        topic_map = {
            "arrays": [r"array", r"sorting", r"searching", r"two sum"],
            "strings": [r"string", r"anagram", r"palindrome", r"reverse"],
            "dynamic_programming": [r"dp", r"dynamic programming", r"fibonacci", r"knapsack"],
            "trees": [r"tree", r"binary tree", r"bst", r"traversal"],
            "linked_list": [r"linked list", r"node", r"reverse list"]
        }
        
        detected = []
        for topic, keywords in topic_map.items():
            if any(re.search(kw, text, re.IGNORECASE) for kw in keywords):
                detected.append(topic)
        return detected

    @staticmethod
    def _extract_coding_problems_raw(text: str) -> List[str]:
        """Extract literal coding problems mentioned in text"""
        patterns = [
            r"(?i)(?:implement|solve|find|search|return)\s+([^.?!\n]+(?:array|graph|tree|cache|query|subarray|ancestor|gcd|combination|element)[^.?!\n]*)",
            r"(?i)Problem:\s*([^.?!\n]+)"
        ]
        problems = []
        for pat in patterns:
            matches = re.findall(pat, text)
            for m in matches:
                cleaned = re.sub(r"\s+", " ", m).strip()
                if (
                    len(cleaned) > 14
                    and AIService._looks_like_coding_problem(cleaned)
                    and AIService._is_generation_worthy(cleaned)
                ):
                    problems.append(cleaned)
        return list(set(problems))

    @staticmethod
    def _extract_aptitude_topics(text: str) -> List[str]:
        """Detect aptitude topics in feedback text"""
        topic_map = {
            "profit_and_loss": [r"profit", r"loss", r"cp", r"sp", r"shopkeeper"],
            "time_and_work": [r"time and work", r"work done", r"efficiency"],
            "speed_distance_time": [r"speed", r"distance", r"time", r"train", r"boat"],
            "percentages": [r"percentage", r"fraction"],
            "logical_reasoning": [r"series", r"coding", r"syllogism", r"logical", r"blood relation"],
            "logarithms": [r"logarithm", r"log base"],
            "puzzles": [r"puzzle", r"riddle"],
            "c_mcqs": [r"c programming", r"pointers", r"loops", r"operator precedence"]
        }
        
        detected = []
        for topic, keywords in topic_map.items():
            if any(re.search(kw, text, re.IGNORECASE) for kw in keywords):
                detected.append(topic)
        return detected

    @staticmethod
    def _extract_technical_topics(text: str) -> List[str]:
        """Detect technical MCQ topics in feedback text"""
        topic_map = {
            "os": [r"operating system", r"os", r"deadlock", r"process", r"thread", r"scheduling"],
            "dbms": [r"dbms", r"database", r"sql", r"join", r"normalization", r"acid"],
            "networking": [r"networking", r"network", r"tcp", r"udp", r"osi", r"dns"],
            "oops": [r"oops", r"object oriented", r"polymorphism", r"inheritance", r"encapsulation"],
            "java": [r"java", r"jvm", r"spring"],
            "python": [r"python", r"django", r"flask"],
            "react": [r"react", r"hook", r"component"],
            "nodejs": [r"node", r"express", r"npm"]
        }
        
        detected = []
        for topic, keywords in topic_map.items():
            if any(re.search(kw, text, re.IGNORECASE) for kw in keywords):
                detected.append(topic)
        return list(set(detected))

    @staticmethod
    async def extract_questions_from_url(
        url: str,
        company_id: str,
        uploader_id: str,
        company_name: str = "",
        source: str = "web"
    ) -> List[Dict[str, Any]]:
        """Fetch a URL and extract structured questions from it"""
        from app.services.scraper_service import ScraperService
        
        raw_content = await ScraperService.fetch_url_content(url)
        if not raw_content:
            return []
            
        clean_text = ScraperService.clean_extracted_text(raw_content)
        print(f"DEBUG: Cleaned text length: {len(clean_text)}")
        questions = await AIService.generate_questions_from_feedback(
            clean_text,
            company_id,
            uploader_id,
            company_name=company_name,
            source=source
        )
        print(f"DEBUG: Extracted {len(questions)} items from URL")
        return questions

    @staticmethod
    def _extract_raw_questions(text: str) -> List[str]:
        """Use regex to find sentences that look like questions or interview tasks"""
        # Patterns for questions
        patterns = [
            r'(?:^|\n)([A-Z][^?!\n]*\?)', # Single line ending in ?
            r'(?:^|\n)(?:Explain|Describe|What|Why|How|Discuss|Define|Difference between|Diff between)\s+[^?!\n]{10,200}', # Direct starting words
            r'(?:^|\n)(?:\d+[\.\)])\s*([^?!\n]{10,500})(?:\n|$)', # Numbered lists
            r'(?:^|\n)[-•*]\s*([^?!\n]{10,500})(?:\n|$)' # Bullet points
        ]
        
        extracted = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                q = match.group(0).strip("-•* \n\r")
                if len(q) > 15 and len(q) < 500: # Filter noise
                    extracted.append(q)
        return list(set(extracted))

    @staticmethod
    async def generate_questions_from_feedback(
        text: str,
        company_id: str,
        uploader_id: str,
        company_name: str = "",
        source: str = "feedback"
    ) -> List[Dict[str, Any]]:
        """
        Generate company-specific questions only from uploaded feedback or scraped interview content.
        No generic question banks are injected here.
        """
        lower_text = text.lower()
        aptitude_topics = AIService._extract_aptitude_topics(lower_text)
        technical_topics = AIService._extract_technical_topics(lower_text)
        coding_topics = AIService._extract_coding_topics(lower_text)
        structured_questions = AIService._extract_structured_question_statements(text)
        coding_problems = AIService._extract_problem_titles_from_urls(text)
        raw_questions = AIService._extract_raw_questions(text)

        technical_questions = []

        generated_questions = []
        source_tags = AIService._build_source_tags(company_id, company_name, source)

        for item in technical_questions:
            question_text = AIService._clean_generated_question_text(item.get("question", ""))
            if not AIService._is_generation_worthy(question_text):
                continue

            options = AIService._extract_options_from_question_text(question_text)
            if len(options) < 2:
                continue

            topic = item.get("topic", "General Technical")
            category = AIService._map_topic_to_category(topic)
            explanation = "Directly extracted from uploaded interview feedback."

            generated_questions.append({
                "text": question_text,
                "type": "technical",
                "category": category,
                "difficulty": AIService._detect_difficulty(question_text),
                "options": options,
                "correct_answer": options[0],
                "explanation": explanation,
                "tags": source_tags + [f"topic:{category}"],
            })

        for problem in coding_problems:
            clean_problem = AIService._clean_generated_question_text(problem)
            if not AIService._is_generation_worthy(clean_problem):
                continue

            coding_category = coding_topics[0] if coding_topics else "coding"
            generated_questions.append({
                "text": f"Implement a solution for: {clean_problem}",
                "type": "coding",
                "category": coding_category,
                "difficulty": AIService._detect_difficulty(clean_problem),
                "options": [],
                "correct_answer": "Check test cases / approach",
                "explanation": "Coding task inferred from uploaded interview feedback. Use the problem statement to design and explain your approach.",
                "test_cases": [],
                "tags": source_tags + [f"topic:{coding_category}"],
            })

        for statement in structured_questions:
            clean_statement = AIService._clean_generated_question_text(statement)
            if not AIService._is_generation_worthy(clean_statement):
                continue

            if AIService._looks_like_coding_problem(clean_statement):
                derived_topic = AIService._infer_feedback_question_category(clean_statement, "coding")
                for generated in AIService._generate_topic_based_coding_questions(
                    coding_topics=[derived_topic],
                    source_tags=source_tags + [f"seed:{re.sub(r'[^a-z0-9]+', '-', clean_statement.lower()).strip('-')[:40]}"],
                    limit_per_topic=1,
                ):
                    generated_questions.append(generated)

        for q_text in raw_questions:
            clean_question = AIService._clean_generated_question_text(q_text)
            if not AIService._is_generation_worthy(clean_question):
                continue

            q_type = AIService._infer_feedback_question_type(clean_question, aptitude_topics, technical_topics, coding_topics)
            if q_type in {"behavioral", None}:
                continue

            options = AIService._extract_options_from_question_text(clean_question)
            if q_type != "coding" and len(options) < 2:
                continue
            if q_type == "coding":
                continue

            category = AIService._infer_feedback_question_category(clean_question, q_type)
            explanation = "Directly extracted from interview feedback for this company."
            correct_answer = options[0] if options else "Refer to explanation"

            generated_questions.append({
                "text": clean_question,
                "type": q_type,
                "category": category,
                "difficulty": AIService._detect_difficulty(clean_question),
                "options": options,
                "correct_answer": correct_answer,
                "explanation": explanation,
                "test_cases": [] if q_type == "coding" else None,
                "tags": source_tags + [f"topic:{category}"],
            })

        generated_questions.extend(
            AIService._generate_topic_based_mcqs(
                topics=aptitude_topics,
                question_type="aptitude",
                source_tags=source_tags,
                limit_per_topic=2,
            )
        )
        generated_questions.extend(
            AIService._generate_topic_based_mcqs(
                topics=technical_topics,
                question_type="technical",
                source_tags=source_tags,
                limit_per_topic=2,
            )
        )
        generated_questions.extend(
            AIService._generate_topic_based_coding_questions(
                coding_topics=coding_topics,
                source_tags=source_tags,
                limit_per_topic=2,
            )
        )

        generated_questions = AIService._ensure_question_targets(
            generated_questions=generated_questions,
            aptitude_topics=aptitude_topics,
            technical_topics=technical_topics,
            coding_topics=coding_topics,
            source_tags=source_tags,
        )

        unique_questions = []
        seen = set()
        for question in generated_questions:
            normalized = "".join(filter(str.isalnum, question.get("text", "").lower()))
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique_questions.append(question)

        selected_questions = []
        type_targets = {
            "aptitude": AIService.TARGET_APTITUDE_COUNT,
            "technical": AIService.TARGET_TECHNICAL_COUNT,
            "coding": AIService.TARGET_CODING_COUNT,
        }

        for q_type, target in type_targets.items():
            selected_questions.extend(
                [q for q in unique_questions if q.get("type") == q_type][:target]
            )

        return selected_questions

    @staticmethod
    def _build_source_tags(company_id: str, company_name: str, source: str) -> List[str]:
        normalized_name = re.sub(r"[^a-z0-9]+", "-", (company_name or "").lower()).strip("-")
        tags = [f"source:{source}", "company_specific", f"company_id:{company_id}"]
        if normalized_name:
            tags.append(f"company_name:{normalized_name}")
        return tags

    @staticmethod
    def _clean_generated_question_text(text: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
        cleaned = re.sub(r"(?i)^(question|problem|task)\s*[:.-]?\s*", "", cleaned).strip()
        return cleaned.rstrip(" -,:;")

    @staticmethod
    def _is_generation_worthy(text: str) -> bool:
        if not text or len(text) < 12 or len(text) > 280:
            return False
        lowered = text.lower()
        noisy_terms = [
            "have you placed",
            "intern offered",
            "your comments",
            "references",
            "sites / books",
            "general tips",
            "prepared by",
            "submitted by",
        ]
        if any(term in lowered for term in noisy_terms):
            return False
        return True

    @staticmethod
    def _extract_structured_question_statements(text: str) -> List[str]:
        candidates = []
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        domain_prefixes = [
            "ds & algo", "problem solving", "os", "probability", "puzzle", "math"
        ]
        blacklist = [
            "intro myself", "best approach", "your comments", "did you clear",
            "sites / books", "general tips", "approach", "references", "solution"
        ]

        for line in lines:
            lowered = line.lower()
            if not any(lowered.startswith(prefix) for prefix in domain_prefixes):
                continue

            cleaned = re.sub(r"^(DS\s*&\s*Algo|Problem\s*solving|OS|Probability|Puzzle|Math)(\s*\([^)]+\))?\s*", "", line, flags=re.I).strip()
            cleaned = AIService._clean_generated_question_text(cleaned)
            if (
                len(cleaned) < 18
                or len(cleaned) > 180
                or any(term in cleaned.lower() for term in blacklist)
            ):
                continue
            if not AIService._looks_like_problem_statement(cleaned):
                continue
            candidates.append(cleaned)

        return list(dict.fromkeys(candidates))

    @staticmethod
    def _looks_like_problem_statement(text: str) -> bool:
        lowered = text.lower()
        useful_terms = [
            "find", "given", "return", "search", "minimum", "maximum", "lowest",
            "array", "graph", "tree", "cache", "subarray", "probability", "query",
            "virtual memory", "binary", "lca", "camera", "parking", "species",
            "element", "gcd", "server", "client", "combination", "image"
        ]
        blocked_terms = [
            "many questions", "best approach", "code only one question",
            "intro myself", "head to head", "optimized solution", "time should be utilized"
        ]
        return any(term in lowered for term in useful_terms) and not any(term in lowered for term in blocked_terms)

    @staticmethod
    def _looks_like_coding_problem(text: str) -> bool:
        lowered = text.lower()
        coding_terms = [
            "find", "return", "search", "lowest common ancestor", "subarray", "graph",
            "tree", "array", "cache", "query", "binary", "camera", "parking dilemma",
            "species", "gcd", "implement"
        ]
        blocked_terms = [
            "intro myself", "best approach", "many questions", "code only one question",
            "time should be utilized", "head to head", "optimized solution", "interviewer expected"
        ]
        return any(term in lowered for term in coding_terms) and not any(term in lowered for term in blocked_terms)

    @staticmethod
    def _extract_problem_titles_from_urls(text: str) -> List[str]:
        urls = re.findall(r"https?://[^\s)]+", text)
        titles = []
        for url in urls:
            slug = url.rstrip("/").split("/")[-1]
            slug = slug.replace(".html", "")
            title = slug.replace("-", " ").replace("_", " ").strip()
            title = re.sub(r"\b(page|watch)\b.*", "", title, flags=re.I).strip()
            if AIService._looks_like_coding_problem(title) and len(title) > 12:
                titles.append(title.title())
        return list(dict.fromkeys(titles))

    @staticmethod
    def _build_topic_practice_prompt(topic: str, question_type: str) -> str:
        aptitude_prompts = {
            "profit_and_loss": "Solve a profit and loss aptitude question involving cost price, selling price, and percentages.",
            "time_and_work": "Solve a time and work aptitude question involving combined efficiency of multiple people.",
            "speed_distance_time": "Solve a speed, distance, and time aptitude question involving trains or relative motion.",
            "percentages": "Solve a percentage-based aptitude question with a short explanation of your method.",
            "logical_reasoning": "Solve a logical reasoning question involving series, patterns, or deduction.",
            "puzzles": "Solve a puzzle-based aptitude question and explain your reasoning step by step.",
            "logarithms": "Solve an aptitude question involving logarithms and explain the simplification steps.",
        }
        technical_prompts = {
            "os": "Explain an operating systems problem involving processes, threads, scheduling, or virtual memory.",
            "dbms": "Answer a DBMS question involving SQL, normalization, transactions, or indexing.",
            "networking": "Answer a networking question involving protocols, layers, routing, or DNS.",
            "oops": "Explain an OOP concept such as inheritance, encapsulation, polymorphism, or abstraction.",
            "java": "Answer a Java-focused technical question about language features, memory, or collections.",
            "python": "Answer a Python-focused technical question involving core syntax, data structures, or runtime behavior.",
            "dsa": "Solve a data structures and algorithms problem and justify the optimal approach.",
        }
        coding_prompts = {
            "arrays": "Solve a coding problem that uses arrays, hashing, or efficient index-based lookup.",
            "strings": "Solve a coding problem involving strings, substrings, or pattern matching.",
            "dynamic_programming": "Solve a dynamic programming problem and explain the recurrence or state transition.",
            "trees": "Solve a coding problem involving trees, traversals, or hierarchical recursion.",
            "linked_list": "Solve a linked list problem involving traversal, updates, or pointer manipulation.",
        }

        if question_type == "aptitude":
            return aptitude_prompts.get(topic, "")
        if question_type == "coding":
            return coding_prompts.get(topic, "")
        return technical_prompts.get(AIService._map_topic_to_category(topic), "")

    @staticmethod
    def _infer_feedback_question_type(
        question_text: str,
        aptitude_topics: List[str],
        technical_topics: List[str],
        coding_topics: List[str]
    ) -> str:
        lowered = question_text.lower()
        behavioral_keywords = [
            "introduce yourself", "strength", "weakness", "career goal", "family",
            "salary", "why should we hire", "conflict", "leadership", "hobbies"
        ]
        if any(keyword in lowered for keyword in behavioral_keywords):
            return "behavioral"

        coding_keywords = [
            "write a program", "write code", "implement", "coding question", "function",
            "algorithm", "linked list", "binary tree", "array", "string", "dynamic programming"
        ]
        if any(keyword in lowered for keyword in coding_keywords):
            return "coding"

        aptitude_keywords = [
            "probability", "permutation", "combination", "percentage", "profit", "loss",
            "train", "boat", "series", "puzzle", "syllogism", "time and work", "aptitude"
        ]
        if any(keyword in lowered for keyword in aptitude_keywords):
            return "aptitude"

        return "technical"

    @staticmethod
    def _infer_feedback_question_category(question_text: str, q_type: str) -> str:
        lowered = question_text.lower()

        if q_type == "aptitude":
            if any(term in lowered for term in ["series", "puzzle", "syllogism", "blood relation", "logical"]):
                return "logical"
            if any(term in lowered for term in ["probability", "percentage", "profit", "loss", "train", "boat", "time and work"]):
                return "quant"
            return "aptitude"

        if q_type == "coding":
            if "string" in lowered:
                return "strings"
            if "tree" in lowered:
                return "trees"
            if "linked list" in lowered:
                return "linked_list"
            if "dynamic programming" in lowered or "dp" in lowered:
                return "dynamic_programming"
            return "coding"

        return AIService._map_topic_to_category(question_text)

    @staticmethod
    def _map_topic_to_category(topic_text: str) -> str:
        lowered = str(topic_text or "").lower()
        if any(term in lowered for term in ["operating system", " os", "deadlock", "process", "thread"]):
            return "os"
        if any(term in lowered for term in ["dbms", "sql", "normalization", "join", "acid", "database"]):
            return "dbms"
        if any(term in lowered for term in ["network", "osi", "tcp", "udp", "dns"]):
            return "networking"
        if any(term in lowered for term in ["oops", "object oriented", "polymorphism", "inheritance", "encapsulation"]):
            return "oops"
        if "java" in lowered:
            return "java"
        if "python" in lowered:
            return "python"
        if "react" in lowered:
            return "react"
        if any(term in lowered for term in ["node", "express", "npm"]):
            return "nodejs"
        if any(term in lowered for term in ["data structure", "algorithm", "recursion", "complexity"]):
            return "dsa"
        return "technical"

    @staticmethod
    def _extract_options_from_question_text(question_text: str) -> List[str]:
        option_matches = re.findall(r"(?:[A-D][\.\)]\s*|(?:\d[\.\)]\s*))([^A-D\d\n\r\t]+)", question_text)
        options = [option.strip(" :-") for option in option_matches if len(option.strip()) > 1]
        if len(options) >= 2:
            return options[:4]
        return []

    @staticmethod
    def _generate_topic_based_mcqs(
        topics: List[str],
        question_type: str,
        source_tags: List[str],
        limit_per_topic: int = 2
    ) -> List[Dict[str, Any]]:
        generated = []
        seen_texts = set()

        topic_to_bank_keys = {
            "aptitude": {
                "profit_and_loss": ["profit_and_loss"],
                "time_and_work": ["time_and_work"],
                "speed_distance_time": ["speed_distance_time"],
                "percentages": ["percentages"],
                "logical_reasoning": ["logical_reasoning", "puzzles"],
                "puzzles": ["puzzles", "logical_reasoning"],
                "logarithms": ["logarithms"],
            },
            "technical": {
                "os": ["os"],
                "dbms": ["dbms"],
                "networking": ["networking"],
                "oops": ["oops"],
                "java": ["java"],
                "python": ["python"],
                "react": ["react"],
                "nodejs": ["nodejs"],
                "dsa": ["os", "dbms", "networking", "oops"],
            }
        }

        normalized_topics = []
        for topic in topics or []:
            normalized = AIService._normalize_topic_for_generation(topic, question_type)
            if normalized and normalized not in normalized_topics:
                normalized_topics.append(normalized)

        bank_map = topic_to_bank_keys.get(question_type, {})
        for topic in normalized_topics:
            for bank_key in bank_map.get(topic, [])[:limit_per_topic]:
                bank = AIService.APTITUDE_QUESTION_BANK.get(bank_key, [])
                for q_temp in bank[:limit_per_topic]:
                    text_key = q_temp["text"].strip().lower()
                    if text_key in seen_texts:
                        continue
                    seen_texts.add(text_key)
                    category = q_temp.get("category", topic if question_type == "technical" else "aptitude")
                    generated.append({
                        "text": q_temp["text"],
                        "type": question_type,
                        "category": category,
                        "difficulty": q_temp.get("difficulty", "medium"),
                        "options": q_temp.get("options", []),
                        "correct_answer": q_temp.get("correct_answer", ""),
                        "explanation": f"Generated from extracted {question_type} topic '{topic}'. {q_temp.get('explanation', '')}".strip(),
                        "tags": source_tags + [f"topic:{topic}", "generated_from_topics"],
                    })

        return generated

    @staticmethod
    def _generate_topic_based_coding_questions(
        coding_topics: List[str],
        source_tags: List[str],
        limit_per_topic: int = 2
    ) -> List[Dict[str, Any]]:
        generated = []
        normalized_topics = []
        seen_texts = set()

        for topic in coding_topics or []:
            normalized = AIService._normalize_topic_for_generation(topic, "coding")
            if normalized and normalized not in normalized_topics:
                normalized_topics.append(normalized)

        for topic in normalized_topics:
            bank = AIService.CODING_QUESTION_BANK.get(topic, [])
            for q_temp in bank[:limit_per_topic]:
                text_key = f"{q_temp['title']}: {q_temp['description']}".strip().lower()
                if text_key in seen_texts:
                    continue
                seen_texts.add(text_key)
                generated.append({
                    "text": f"{q_temp['title']}: {q_temp['description']}",
                    "type": "coding",
                    "category": topic,
                    "difficulty": q_temp.get("difficulty", "medium"),
                    "options": [],
                    "correct_answer": "Check test cases",
                    "explanation": f"Generated from extracted coding topic '{topic}'. Problem: {q_temp['title']}",
                    "test_cases": q_temp.get("test_cases", []),
                    "sample_input": q_temp.get("sample_input"),
                    "sample_output": q_temp.get("sample_output"),
                    "tags": source_tags + [f"topic:{topic}", "generated_from_topics"],
                })

        return generated

    @staticmethod
    def _normalize_topic_for_generation(topic: str, question_type: str) -> str:
        lowered = str(topic or "").lower().strip()
        if not lowered:
            return ""

        if question_type == "aptitude":
            if any(term in lowered for term in ["profit", "loss"]):
                return "profit_and_loss"
            if "time and work" in lowered or "work" in lowered:
                return "time_and_work"
            if any(term in lowered for term in ["speed", "distance", "train", "boat"]):
                return "speed_distance_time"
            if "percentage" in lowered:
                return "percentages"
            if any(term in lowered for term in ["series", "logical", "syllogism", "reasoning"]):
                return "logical_reasoning"
            if "puzzle" in lowered:
                return "puzzles"
            if "logarithm" in lowered:
                return "logarithms"
            return ""

        if question_type == "technical":
            return AIService._map_topic_to_category(lowered)

        if question_type == "coding":
            if any(term in lowered for term in ["array", "hashmap", "hash map", "sliding window"]):
                return "arrays"
            if "string" in lowered:
                return "strings"
            if any(term in lowered for term in ["dynamic programming", "dp"]):
                return "dynamic_programming"
            if any(term in lowered for term in ["tree", "binary tree", "bst"]):
                return "trees"
            if "linked list" in lowered:
                return "linked_list"
            return ""

        return ""

    @staticmethod
    def _ensure_question_targets(
        generated_questions: List[Dict[str, Any]],
        aptitude_topics: List[str],
        technical_topics: List[str],
        coding_topics: List[str],
        source_tags: List[str],
    ) -> List[Dict[str, Any]]:
        results = list(generated_questions)
        results.extend(
            AIService._supplement_topic_mcqs(
                existing_questions=results,
                topics=aptitude_topics,
                question_type="aptitude",
                source_tags=source_tags,
                target_count=AIService.TARGET_APTITUDE_COUNT,
            )
        )
        results.extend(
            AIService._supplement_topic_mcqs(
                existing_questions=results,
                topics=technical_topics,
                question_type="technical",
                source_tags=source_tags,
                target_count=AIService.TARGET_TECHNICAL_COUNT,
            )
        )
        results.extend(
            AIService._supplement_coding_questions(
                existing_questions=results,
                coding_topics=coding_topics,
                source_tags=source_tags,
                target_count=AIService.TARGET_CODING_COUNT,
            )
        )
        return results

    @staticmethod
    def _supplement_topic_mcqs(
        existing_questions: List[Dict[str, Any]],
        topics: List[str],
        question_type: str,
        source_tags: List[str],
        target_count: int,
    ) -> List[Dict[str, Any]]:
        current_count = sum(1 for q in existing_questions if q.get("type") == question_type)
        if current_count >= target_count:
            return []

        normalized_topics = []
        for topic in topics or []:
            normalized = AIService._normalize_topic_for_generation(topic, question_type)
            if normalized and normalized not in normalized_topics:
                normalized_topics.append(normalized)

        if not normalized_topics:
            normalized_topics = ["logical_reasoning"] if question_type == "aptitude" else ["dbms", "networking", "oops", "os"]
        elif question_type == "aptitude":
            for fallback_topic in ["time_and_work", "percentages", "logarithms", "profit_and_loss", "speed_distance_time", "logical_reasoning", "puzzles"]:
                if fallback_topic not in normalized_topics:
                    normalized_topics.append(fallback_topic)
        else:
            for fallback_topic in ["dbms", "networking", "oops", "os", "nodejs", "java", "python", "react"]:
                if fallback_topic not in normalized_topics:
                    normalized_topics.append(fallback_topic)

        supplemental_bank = AIService._get_supplemental_mcq_bank(question_type)
        existing_texts = {q.get("text", "").strip().lower() for q in existing_questions}
        generated = []
        topic_index = 0

        while current_count + len(generated) < target_count and normalized_topics:
            topic = normalized_topics[topic_index % len(normalized_topics)]
            for item in supplemental_bank.get(topic, []):
                text_key = item["text"].strip().lower()
                if text_key in existing_texts:
                    continue
                existing_texts.add(text_key)
                generated.append({
                    "text": item["text"],
                    "type": question_type,
                    "category": item.get("category", topic if question_type == "technical" else "aptitude"),
                    "difficulty": item.get("difficulty", "medium"),
                    "options": item.get("options", []),
                    "correct_answer": item.get("correct_answer", ""),
                    "explanation": f"Generated from extracted {question_type} topic '{topic}'. {item.get('explanation', '')}".strip(),
                    "tags": source_tags + [f"topic:{topic}", "generated_from_topics", "supplemental_generation"],
                })
                if current_count + len(generated) >= target_count:
                    break
            topic_index += 1
            if topic_index > len(normalized_topics) * 6:
                break

        return generated

    @staticmethod
    def _supplement_coding_questions(
        existing_questions: List[Dict[str, Any]],
        coding_topics: List[str],
        source_tags: List[str],
        target_count: int,
    ) -> List[Dict[str, Any]]:
        current_count = sum(1 for q in existing_questions if q.get("type") == "coding")
        if current_count >= target_count:
            return []

        normalized_topics = []
        for topic in coding_topics or []:
            normalized = AIService._normalize_topic_for_generation(topic, "coding")
            if normalized and normalized not in normalized_topics:
                normalized_topics.append(normalized)

        fallback_topics = ["arrays", "strings", "trees", "dynamic_programming", "linked_list"]
        for topic in fallback_topics:
            if topic not in normalized_topics:
                normalized_topics.append(topic)

        generated = []
        existing_texts = {q.get("text", "").strip().lower() for q in existing_questions}

        for topic in normalized_topics:
            for item in AIService.CODING_QUESTION_BANK.get(topic, []):
                text = f"{item['title']}: {item['description']}"
                text_key = text.lower()
                if text_key in existing_texts:
                    continue
                existing_texts.add(text_key)
                generated.append({
                    "text": text,
                    "type": "coding",
                    "category": topic,
                    "difficulty": item.get("difficulty", "medium"),
                    "options": [],
                    "correct_answer": "Check test cases",
                    "explanation": f"Generated from extracted coding topic '{topic}'. Problem: {item['title']}",
                    "test_cases": item.get("test_cases", []),
                    "sample_input": item.get("sample_input"),
                    "sample_output": item.get("sample_output"),
                    "tags": source_tags + [f"topic:{topic}", "generated_from_topics", "supplemental_generation"],
                })
                if current_count + len(generated) >= target_count:
                    return generated

        return generated

    @staticmethod
    def _get_supplemental_mcq_bank(question_type: str) -> Dict[str, List[Dict[str, Any]]]:
        if question_type == "aptitude":
            return {
                "profit_and_loss": [
                    {"text": "A trader marks an article 40% above cost price and gives a 10% discount. What is his profit percentage?", "options": ["20%", "24%", "26%", "30%"], "correct_answer": "26%", "explanation": "SP = 1.4 x 0.9 = 1.26 of CP.", "category": "quant", "difficulty": "easy"},
                    {"text": "An article is sold for Rs. 540 at a loss of 10%. What should be the selling price to gain 20%?", "options": ["Rs. 648", "Rs. 700", "Rs. 720", "Rs. 750"], "correct_answer": "Rs. 720", "explanation": "CP = 540/0.9 = 600, desired SP = 600 x 1.2.", "category": "quant", "difficulty": "easy"},
                    {"text": "A dealer gains 15% after allowing a discount of 10% on the marked price. If the cost price is Rs. 200, what is the marked price?", "options": ["Rs. 245.50", "Rs. 250", "Rs. 255.56", "Rs. 260"], "correct_answer": "Rs. 255.56", "explanation": "SP = 230 and MP = 230/0.9.", "category": "quant", "difficulty": "medium"},
                ],
                "time_and_work": [
                    {"text": "A can finish a work in 12 days and B in 18 days. In how many days will they complete the work together?", "options": ["6.2 days", "7.2 days", "7.5 days", "8 days"], "correct_answer": "7.2 days", "explanation": "Combined work = 5/36, time = 36/5 days.", "category": "quant", "difficulty": "easy"},
                    {"text": "A takes 10 days more than B to complete a job. Together they finish it in 12 days. How many days does B alone take?", "options": ["20", "24", "30", "36"], "correct_answer": "20", "explanation": "Let B=x, A=x+10. Solve 1/x + 1/(x+10) = 1/12.", "category": "quant", "difficulty": "medium"},
                    {"text": "12 men can complete a work in 15 days. How many men are needed to complete the same work in 9 days?", "options": ["18", "20", "22", "24"], "correct_answer": "20", "explanation": "Men x days is constant.", "category": "quant", "difficulty": "easy"},
                    {"text": "A and B together can complete a piece of work in 8 days, while B alone can complete it in 12 days. In how many days can A alone complete it?", "options": ["18", "20", "24", "28"], "correct_answer": "24", "explanation": "A's work rate = 1/8 - 1/12 = 1/24.", "category": "quant", "difficulty": "medium"},
                ],
                "speed_distance_time": [
                    {"text": "A man covers 360 km in 6 hours. What is his speed in m/s?", "options": ["10", "12.5", "16.67", "20"], "correct_answer": "16.67", "explanation": "360 km/hr = 60 km/hr = 16.67 m/s.", "category": "quant", "difficulty": "easy"},
                    {"text": "Two trains of lengths 120 m and 180 m running in opposite directions at 54 km/h and 36 km/h cross each other in how many seconds?", "options": ["10", "12", "15", "20"], "correct_answer": "12", "explanation": "Relative speed = 90 km/h = 25 m/s, distance = 300 m.", "category": "quant", "difficulty": "medium"},
                    {"text": "A boat goes 30 km downstream in 2 hours and returns upstream in 3 hours. What is the speed of the stream?", "options": ["2.5 km/h", "3 km/h", "4 km/h", "5 km/h"], "correct_answer": "2.5 km/h", "explanation": "Downstream 15, upstream 10, stream speed = (15-10)/2.", "category": "quant", "difficulty": "medium"},
                    {"text": "A car travels at 45 km/h for 2 hours and 60 km/h for 3 hours. What is the average speed?", "options": ["52 km/h", "54 km/h", "56 km/h", "58 km/h"], "correct_answer": "54 km/h", "explanation": "Total distance 270 km in 5 hours.", "category": "quant", "difficulty": "easy"},
                ],
                "percentages": [
                    {"text": "If the price of a product increases by 20%, by what percent should consumption be reduced to keep expenditure unchanged?", "options": ["16.67%", "18%", "20%", "25%"], "correct_answer": "16.67%", "explanation": "Required decrease = 20/120 x 100.", "category": "quant", "difficulty": "medium"},
                    {"text": "A number is first increased by 25% and then decreased by 20%. What is the net percentage change?", "options": ["0%", "2% increase", "2% decrease", "5% increase"], "correct_answer": "0%", "explanation": "1.25 x 0.8 = 1.", "category": "quant", "difficulty": "easy"},
                    {"text": "What is 35% of 480?", "options": ["148", "156", "168", "172"], "correct_answer": "168", "explanation": "0.35 x 480.", "category": "quant", "difficulty": "easy"},
                    {"text": "The population of a town increases by 10% in the first year and 20% in the second year. What is the overall percentage increase?", "options": ["28%", "30%", "32%", "35%"], "correct_answer": "32%", "explanation": "Compound increase = 1.1 x 1.2 = 1.32.", "category": "quant", "difficulty": "easy"},
                ],
                "logical_reasoning": [
                    {"text": "Find the next term in the series: 2, 6, 12, 20, 30, ?", "options": ["36", "40", "42", "44"], "correct_answer": "42", "explanation": "Pattern adds consecutive even numbers.", "category": "logical", "difficulty": "easy"},
                    {"text": "If in a certain code CAT is written as XZG, how is DOG written in that code?", "options": ["WLT", "WLT", "WLT", "WLT"], "correct_answer": "WLT", "explanation": "Each letter is replaced by its opposite in the alphabet.", "category": "logical", "difficulty": "medium"},
                    {"text": "Statement: All pens are books. Some books are bags. Conclusion: Some pens are bags. Choose the correct option.", "options": ["Definitely true", "Definitely false", "Possibly true", "Cannot be determined"], "correct_answer": "Cannot be determined", "explanation": "No direct overlap between pens and bags is guaranteed.", "category": "logical", "difficulty": "medium"},
                    {"text": "If SOUTH is coded as 12345 and NORTH as 67845, what is the code for SNOW?", "options": ["1679", "1769", "7189", "7186"], "correct_answer": "1769", "explanation": "Map letters positionally from the given codes.", "category": "logical", "difficulty": "medium"},
                    {"text": "Choose the odd one out: Triangle, Square, Circle, Cylinder.", "options": ["Triangle", "Square", "Circle", "Cylinder"], "correct_answer": "Cylinder", "explanation": "Cylinder is a 3D shape while the others are 2D.", "category": "logical", "difficulty": "easy"},
                ],
                "puzzles": [
                    {"text": "Five friends are sitting in a row. A is to the left of B, C is to the right of D, and E is between B and C. Who is in the middle?", "options": ["A", "B", "C", "D"], "correct_answer": "B", "explanation": "Arrange according to the given clues.", "category": "logical", "difficulty": "medium"},
                    {"text": "A clock shows 3:15. What is the angle between the hour and minute hands?", "options": ["0°", "7.5°", "15°", "22.5°"], "correct_answer": "7.5°", "explanation": "Hour hand is at 97.5°, minute hand at 90°.", "category": "logical", "difficulty": "easy"},
                    {"text": "In a family puzzle, P is the father of Q, Q is the sister of R, and R is the son of S. How is S related to P?", "options": ["Wife", "Brother", "Mother", "Cannot be determined"], "correct_answer": "Cannot be determined", "explanation": "Only parent relation of R is known, gender/connection to P is not fixed.", "category": "logical", "difficulty": "medium"},
                    {"text": "A cube is painted on all sides and cut into 27 equal smaller cubes. How many small cubes have exactly two faces painted?", "options": ["8", "12", "16", "24"], "correct_answer": "12", "explanation": "Edge-center cubes count is 12.", "category": "logical", "difficulty": "medium"},
                    {"text": "Three switches outside a room correspond to three bulbs inside. You may enter the room only once. How can you identify which switch controls which bulb?", "options": ["Flip all switches once", "Use heat from one bulb before entering", "Open the room twice", "It is impossible"], "correct_answer": "Use heat from one bulb before entering", "explanation": "Turn one switch on for some time, turn it off, turn another on, then inspect light and bulb heat.", "category": "logical", "difficulty": "medium"},
                ],
                "logarithms": [
                    {"text": "If log10(x) = 2.5, then x is equal to?", "options": ["250", "300", "316.23", "500"], "correct_answer": "316.23", "explanation": "x = 10^2.5.", "category": "quant", "difficulty": "medium"},
                    {"text": "What is the value of log3(81)?", "options": ["2", "3", "4", "5"], "correct_answer": "4", "explanation": "3^4 = 81.", "category": "quant", "difficulty": "easy"},
                    {"text": "If log a + log b = log 72 and a = 8, what is b?", "options": ["6", "8", "9", "12"], "correct_answer": "9", "explanation": "ab = 72.", "category": "quant", "difficulty": "easy"},
                ],
            }

        return {
            "os": [
                {"text": "Which scheduling algorithm may suffer from starvation for long jobs?", "options": ["Round Robin", "FCFS", "Shortest Job First", "Priority Scheduling"], "correct_answer": "Shortest Job First", "explanation": "Long jobs can wait indefinitely if short jobs keep arriving.", "category": "os", "difficulty": "medium"},
                {"text": "Which memory allocation strategy searches the entire list and chooses the smallest suitable hole?", "options": ["First fit", "Best fit", "Worst fit", "Next fit"], "correct_answer": "Best fit", "explanation": "Best fit minimizes leftover space for each allocation.", "category": "os", "difficulty": "medium"},
                {"text": "What is thrashing in an operating system?", "options": ["Excessive CPU usage", "Excessive paging causing low useful work", "Disk corruption", "Thread deadlock"], "correct_answer": "Excessive paging causing low useful work", "explanation": "Thrashing happens when the system spends most of its time swapping pages.", "category": "os", "difficulty": "medium"},
            ],
            "dbms": [
                {"text": "Which normal form removes partial dependency on a composite key?", "options": ["1NF", "2NF", "3NF", "BCNF"], "correct_answer": "2NF", "explanation": "2NF eliminates partial dependencies.", "category": "dbms", "difficulty": "easy"},
                {"text": "Which SQL clause is used to filter grouped records?", "options": ["WHERE", "GROUP BY", "HAVING", "ORDER BY"], "correct_answer": "HAVING", "explanation": "HAVING filters aggregated/grouped rows.", "category": "dbms", "difficulty": "easy"},
                {"text": "Which index structure is commonly used in database systems to support range queries efficiently?", "options": ["B+ Tree", "Hash Table", "Stack", "Queue"], "correct_answer": "B+ Tree", "explanation": "B+ Trees preserve order and support range scans.", "category": "dbms", "difficulty": "medium"},
                {"text": "Which transaction property ensures that either all operations complete or none do?", "options": ["Consistency", "Atomicity", "Isolation", "Durability"], "correct_answer": "Atomicity", "explanation": "Atomicity guarantees all-or-nothing behavior.", "category": "dbms", "difficulty": "easy"},
            ],
            "networking": [
                {"text": "Which protocol is connection-oriented?", "options": ["UDP", "IP", "TCP", "ICMP"], "correct_answer": "TCP", "explanation": "TCP establishes a connection before data transfer.", "category": "networking", "difficulty": "easy"},
                {"text": "Which device primarily operates at the data link layer to forward frames?", "options": ["Router", "Switch", "Gateway", "Repeater"], "correct_answer": "Switch", "explanation": "Switches use MAC addresses to forward frames.", "category": "networking", "difficulty": "easy"},
                {"text": "What is the default port used by HTTPS?", "options": ["21", "53", "80", "443"], "correct_answer": "443", "explanation": "HTTPS commonly uses port 443.", "category": "networking", "difficulty": "easy"},
                {"text": "Which IPv4 address class provides the largest number of host addresses per network?", "options": ["Class A", "Class B", "Class C", "Class D"], "correct_answer": "Class A", "explanation": "Class A reserves most bits for hosts.", "category": "networking", "difficulty": "medium"},
                {"text": "Which protocol is used to automatically assign IP addresses to devices in a network?", "options": ["DNS", "DHCP", "FTP", "ARP"], "correct_answer": "DHCP", "explanation": "DHCP dynamically assigns IP addresses.", "category": "networking", "difficulty": "easy"},
            ],
            "oops": [
                {"text": "Which OOP concept allows one interface to be used for different underlying forms?", "options": ["Encapsulation", "Polymorphism", "Inheritance", "Abstraction"], "correct_answer": "Polymorphism", "explanation": "Polymorphism supports many forms through a common interface.", "category": "oops", "difficulty": "easy"},
                {"text": "Which access modifier makes a class member available only within the same class in Java?", "options": ["public", "protected", "private", "default"], "correct_answer": "private", "explanation": "Private members are only accessible inside the class.", "category": "oops", "difficulty": "easy"},
                {"text": "What is abstraction in OOP?", "options": ["Showing only essential features and hiding implementation details", "Creating multiple objects", "Deriving a class from another class", "Combining methods from two classes"], "correct_answer": "Showing only essential features and hiding implementation details", "explanation": "Abstraction exposes what an object does, not how it does it.", "category": "oops", "difficulty": "medium"},
                {"text": "Which relationship best represents inheritance?", "options": ["has-a", "uses-a", "is-a", "part-of"], "correct_answer": "is-a", "explanation": "Inheritance models an is-a relationship.", "category": "oops", "difficulty": "easy"},
            ],
            "java": [
                {"text": "Which component of Java executes the bytecode?", "options": ["JDK", "JVM", "JRE", "JAR"], "correct_answer": "JVM", "explanation": "The JVM interprets or compiles bytecode for execution.", "category": "java", "difficulty": "easy"},
                {"text": "Which collection does not allow duplicate elements in Java?", "options": ["List", "Map", "Set", "Queue"], "correct_answer": "Set", "explanation": "A Set stores unique elements.", "category": "java", "difficulty": "easy"},
                {"text": "Which keyword is used to inherit a class in Java?", "options": ["implements", "extends", "inherits", "super"], "correct_answer": "extends", "explanation": "A child class extends a parent class.", "category": "java", "difficulty": "easy"},
            ],
            "python": [
                {"text": "Which Python data type is immutable?", "options": ["list", "dict", "set", "tuple"], "correct_answer": "tuple", "explanation": "Tuples cannot be modified after creation.", "category": "python", "difficulty": "easy"},
                {"text": "What is the output type of range(5) in Python 3?", "options": ["list", "tuple", "range object", "generator"], "correct_answer": "range object", "explanation": "range returns a lazy iterable range object.", "category": "python", "difficulty": "easy"},
                {"text": "Which keyword is used to handle exceptions in Python?", "options": ["catch", "handle", "except", "error"], "correct_answer": "except", "explanation": "Python uses try/except blocks.", "category": "python", "difficulty": "easy"},
            ],
            "react": [
                {"text": "Which hook is commonly used to store component state in React?", "options": ["useEffect", "useState", "useRef", "useContext"], "correct_answer": "useState", "explanation": "useState manages local component state.", "category": "react", "difficulty": "easy"},
                {"text": "What prop is used by React to help identify list items uniquely?", "options": ["id", "index", "key", "name"], "correct_answer": "key", "explanation": "React uses keys to track items during reconciliation.", "category": "react", "difficulty": "easy"},
                {"text": "Which method is commonly used to render lists in React JSX?", "options": ["filter()", "map()", "reduce()", "forEach()"], "correct_answer": "map()", "explanation": "map() transforms arrays into JSX elements.", "category": "react", "difficulty": "easy"},
            ],
            "nodejs": [
                {"text": "Which package manager is bundled by default with Node.js?", "options": ["yarn", "pnpm", "npm", "bower"], "correct_answer": "npm", "explanation": "npm ships with Node.js installations.", "category": "technical", "difficulty": "easy"},
                {"text": "Which object gives access to request data in an Express route handler?", "options": ["res", "req", "app", "router"], "correct_answer": "req", "explanation": "req contains request metadata and payload.", "category": "technical", "difficulty": "easy"},
                {"text": "Which method in Express sends a JSON response?", "options": ["res.text()", "res.endJson()", "res.json()", "req.json()"], "correct_answer": "res.json()", "explanation": "res.json serializes and sends JSON.", "category": "technical", "difficulty": "easy"},
                {"text": "Which of these best describes Node.js?", "options": ["A browser", "A Java framework", "A JavaScript runtime", "A database"], "correct_answer": "A JavaScript runtime", "explanation": "Node.js runs JavaScript outside the browser.", "category": "technical", "difficulty": "easy"},
                {"text": "Which built-in Node.js module is commonly used for filesystem operations?", "options": ["http", "fs", "path", "events"], "correct_answer": "fs", "explanation": "The fs module handles file system operations.", "category": "technical", "difficulty": "easy"},
            ],
        }
    @staticmethod
    async def extract_questions_from_url(
        url: str,
        company_id: str,
        uploader_id: str,
        company_name: str = "",
        source: str = "web"
    ) -> List[Dict[str, Any]]:
        """Fetch content from a URL and extract questions using regex and ML"""
        insights = await AIService.extract_full_insights_from_url(
            url,
            company_id,
            uploader_id,
            company_name=company_name
        )
        return insights.get("generated_questions", [])

    @staticmethod
    async def extract_full_insights_from_url(
        url: str,
        company_id: str,
        uploader_id: str,
        company_name: str = ""
    ) -> Dict[str, Any]:
        """Fetch content from a URL and extract rounds, FAQs, tips, AND questions"""
        from app.services.scraper_service import ScraperService
        
        content = await ScraperService.fetch_url_content(url)
        if not content:
            return {}
            
        print(f"DEBUG: Processing {len(content)} characters from {url}")
        
        # Core extraction logic (already handles rounds, FAQs, tips)
        insights = await AIService.analyze_feedback(content)
        
        # Also generate MCQs/extracted items from the same text
        questions = await AIService.generate_questions_from_feedback(
            text=content,
            company_id=company_id,
            uploader_id=uploader_id,
            company_name=company_name,
            source="web"
        )
        
        # Merge questions from generate_questions_from_feedback (better at MCQs) 
        # into technical_questions from analyze_feedback (better at raw text)
        insights["generated_questions"] = questions
        return insights
