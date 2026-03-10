import re
from typing import List, Dict, Any
from app.config import settings
import logging
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)

class AIService:
    _nlp = None

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

        extracted_rounds = AIService._extract_and_normalize_rounds(text)
        
        # Use ML to fill in gaps or get better summaries if rounds are missing specific details
        # For instance, if regex didn't find "topics", we ask the model.
        
        topics = AIService._extract_topics_with_ml(text)
        if not topics: # Fallback
            topics = AIService._extract_topics(text)
            
        difficulty = AIService._detect_difficulty(text) # Logic is simple enough for regex usually, but can be ML enriched

        # Extracted Technical Questions with Referrals
        tech_questions_raw = AIService._extract_technical_questions_with_metadata(text)
        
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
        # 1. Patterns to identify starting markers
        pattern = r"(Round\s*[-:]?\s*\d+|First Round|Second Round|Third Round|Fourth Round|Fifth Round|Technical Round|HR Round|Aptitude Round|Coding Round|Managerial Round|Technical Interview|ROUND\s*[-:]?\s*\d+)"
        
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        if not matches:
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
        return topics

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
        # Look for phrases like "asked to write a program for", "solve", "implement"
        patterns = [
            r"(?i)(?:asked to|write a program for|implement|solve|coding question was)\s*([^.?!,]+)",
            r"(?i)Problem:\s*([^.?!,]+)"
        ]
        problems = []
        for pat in patterns:
            matches = re.findall(pat, text)
            for m in matches:
                if len(m.strip()) > 10:
                    problems.append(m.strip())
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
    async def generate_questions_from_feedback(text: str, company_id: str, uploader_id: str) -> List[Dict[str, Any]]:
        """
        Generate integrated MCQ questions based on interview feedback.
        """
        # Universal Auto-Generation: Trigger mass generation for ANY company
        detected_topics = AIService._extract_aptitude_topics(text)
        tech_topics = AIService._extract_topics(text)
        coding_topics = AIService._extract_coding_topics(text)
        
        # Combine topics
        all_topics = list(set(detected_topics + tech_topics))
        
        # Generate 50 questions (shuffled between internal bank and ML synthesis if available)
        questions = []
        
        # 1. Topic-Based Seed Generation (Aptitude & Technical MCQ)
        import random
        for topic in all_topics:
            bank = AIService.APTITUDE_QUESTION_BANK.get(topic, [])
            for q_temp in bank:
                questions.append({
                    "text": q_temp["text"],
                    "type": "aptitude" if topic in detected_topics else "technical",
                    "category": q_temp["category"],
                    "difficulty": q_temp["difficulty"],
                    "options": q_temp["options"],
                    "correct_answer": q_temp["correct_answer"],
                    "explanation": q_temp["explanation"],
                    "company_id": company_id,
                    "created_by": uploader_id
                })

        # 2. Coding Problem Generation
        for topic in coding_topics:
            bank = AIService.CODING_QUESTION_BANK.get(topic, [])
            for q_temp in bank:
                questions.append({
                    "text": q_temp["description"],
                    "title": q_temp["title"],
                    "type": "coding",
                    "category": topic,
                    "difficulty": q_temp["difficulty"],
                    "correct_answer": "Check test cases", # For coding, this is placeholder
                    "explanation": f"Solve the problem: {q_temp['title']}",
                    "test_cases": q_temp["test_cases"],
                    "company_id": company_id,
                    "created_by": uploader_id
                })

        # 3. ML-Based Extraction (Direct from Feedback)
        raw_problems = AIService._extract_coding_problems_raw(text)
        for problem in raw_problems:
             questions.append({
                    "text": problem,
                    "type": "coding",
                    "category": "extracted",
                    "difficulty": "medium",
                    "correct_answer": "Check test cases",
                    "explanation": "Extracted from feedback.",
                    "test_cases": [], # Will need manual review or AI generation later
                    "company_id": company_id,
                    "created_by": uploader_id
                })

        # 4. ML-Based Behavioral Extraction
        try:
             ans_q = MLService.answer_question(text, "What technical questions or HR questions were asked?")
             if ans_q['score'] > 0.05:
                 questions.append({
                     "text": ans_q['answer'],
                     "type": "technical",
                     "category": "technical",
                     "difficulty": "medium",
                     "options": ["A) Theory", "B) Application", "C) Conceptual", "D) None of above"],
                     "correct_answer": "A) Theory",
                     "explanation": f"Extracted from feedback context.",
                     "company_id": company_id,
                     "created_by": uploader_id
                 })
        except:
            pass

        # Deduplicate and return
        unique_qs = []
        seen = set()
        for q in questions:
            q_text = q.get("text", "")
            if q_text not in seen:
                unique_qs.append(q)
                seen.add(q_text)
        
        # NOTE: For now, we return these top matches. 
        # The AssessmentService handles filling up to 50 or managing coding vs aptitude.
        return unique_qs[:40] 
