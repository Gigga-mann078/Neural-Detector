# -*- coding:utf-8 -*-
import re
import math
import random
from statistics import mean, stdev
import numpy as np
import torch
import torch.nn as nn
from typing import List, Dict, Tuple, Optional
import warnings
import subprocess
import langid
warnings.filterwarnings('ignore')


class LanguageSurgeon:
    def __init__(self, use_gpu: bool = False):
        self.lang_map = {
            'en': 'en', 'ru': 'ru', 'es': 'es', 'fr': 'fr', 'de': 'de',
            'it': 'it', 'pt': 'pt', 'nl': 'nl', 'sv': 'sv', 'no': 'no',
            'da': 'da', 'fi': 'fi', 'pl': 'pl', 'cs': 'cs', 'sk': 'sk',
            'hu': 'hu', 'ro': 'ro', 'bg': 'bg', 'sr': 'sr', 'hr': 'hr',
            'el': 'el', 'tr': 'tr', 'ar': 'ar', 'he': 'he', 'ja': 'ja',
            'zh': 'zh', 'ko': 'ko'
        }

    def detect_language(self, text: str) -> Dict:
        if len(text.strip()) < 10:
            return {'language': 'unknown', 'confidence': 0.0, 'method': 'none'}

        try:
            lang, confidence = langid.classify(text)
            mapped_lang = self.lang_map.get(lang, lang)

            return {
                'language': mapped_lang,
                'confidence': float(confidence),
                'method': 'langid',
                'raw_lang': lang
            }
        except Exception as e:
            return {'language': 'unknown', 'confidence': 0.0, 'method': 'error', 'error': str(e)}


class EmbeddingSurgeon:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        self.language_models = {
            'en': SentenceTransformer('all-MiniLM-L6-v2'),
            'ru': SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'),
        }

    def embed(self, text: str, language: str = None) -> np.ndarray:
        if language and language in self.language_models:
            return self.language_models[language].encode(text)
        return self.model.encode(text)


class MultilingualPerplexitySurgeon:
    def __init__(self):
        self.models = {}

    def load_model(self, language: str):
        if language not in self.models:
            try:
                if language == 'en':
                    from transformers import GPT2LMHeadModel, GPT2TokenizerFast
                    self.models[language] = {
                        'model': GPT2LMHeadModel.from_pretrained('gpt2'),
                        'tokenizer': GPT2TokenizerFast.from_pretrained('gpt2')
                    }
                elif language == 'ru':
                    from transformers import AutoModelForCausalLM, AutoTokenizer
                    self.models[language] = {
                        'model': AutoModelForCausalLM.from_pretrained('sberbank-ai/rugpt3small_based_on_gpt2'),
                        'tokenizer': AutoTokenizer.from_pretrained('sberbank-ai/rugpt3small_based_on_gpt2')
                    }
            except Exception as e:
                print(f"Model load error ({language}): {e}")
                return None
        return self.models[language]

    def calculate_perplexity(self, text: str, language: str = 'en') -> Dict:
        model_data = self.load_model(language)
        if not model_data:
            return {'perplexity': None, 'error': 'Model not available'}

        model = model_data['model']
        tokenizer = model_data['tokenizer']
        model.eval()

        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)

        with torch.no_grad():
            outputs = model(**inputs, labels=inputs['input_ids'])
            loss = outputs.loss
            perplexity = torch.exp(loss).item()

            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)

            token_probs = probs[0, torch.arange(inputs['input_ids'].shape[1]), inputs['input_ids'][0]]
            avg_prob = token_probs.mean().item()
            entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1).mean().item()

        return {
            'perplexity': perplexity,
            'avg_token_probability': avg_prob,
            'entropy': entropy,
            'token_count': inputs['input_ids'].shape[1]
        }


class StylometricSurgeon:
    def analyze(self, text: str) -> Dict:
        import re
        from collections import Counter

        words = text.split()
        word_count = len(words)
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])

        word_lengths = [len(w) for w in words]
        avg_word_len = np.mean(word_lengths) if word_lengths else 0

        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        avg_sent_len = np.mean(sentence_lengths) if sentence_lengths else 0

        char_freq = Counter(text.lower())
        top_chars = char_freq.most_common(10)

        punctuation = '.,!?;:'
        punct_count = sum(text.count(p) for p in punctuation)

        unique_words = len(set(words))
        lexical_diversity = unique_words / word_count if word_count > 0 else 0

        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_word_length': avg_word_len,
            'avg_sentence_length': avg_sent_len,
            'punctuation_count': punct_count,
            'lexical_diversity': lexical_diversity,
            'top_characters': top_chars
        }


class AIPatternSurgeon:
    def __init__(self):
        self.patterns = {
            'en': [
                r'(?i)\bit is important to note\b', r'(?i)\bin conclusion\b',
                r'(?i)\boverall\b', r'(?i)\bas we can see\b', r'(?i)\bmoreover\b',
                r'(?i)\bfurthermore\b', r'(?i)\btherefore\b', r'(?i)\bhowever\b',
                r'(?i)\bthus\b', r'(?i)\bconsequently\b'
            ],
            'ru': [
                r'(?i)\bследовательно\b', r'(?i)\bтаким образом\b', r'(?i)\bитак\b',
                r'(?i)\bв заключение\b', r'(?i)\bкроме того\b', r'(?i)\bоднако\b',
                r'(?i)\bпоэтому\b', r'(?i)\bв результате\b', r'(?i)\bподводя итоги\b',
                r'(?i)\bважно отметить\b'
            ],
            'es': [
                r'(?i)\ben conclusión\b', r'(?i)\bpor lo tanto\b', r'(?i)\bsin embargo\b',
                r'(?i)\bademás\b', r'(?i)\bes importante señalar\b', r'(?i)\ben resumen\b',
                r'(?i)\bcomo podemos ver\b', r'(?i)\bpor consiguiente\b',
                r'(?i)\bno obstante\b', r'(?i)\ben definitiva\b'
            ],
            'fr': [
                r'(?i)\ben conclusion\b', r'(?i)\bpar conséquent\b', r'(?i)\bcependant\b',
                r'(?i)\bde plus\b', r'(?i)\bil est important de noter\b', r'(?i)\ben résumé\b',
                r'(?i)\bainsi\b', r'(?i)\bpar ailleurs\b', r'(?i)\bnéanmoins\b',
                r'(?i)\bpour conclure\b'
            ],
            'de': [
                r'(?i)\bzusammenfassend\b', r'(?i)\bfolglich\b', r'(?i)\ballerdings\b',
                r'(?i)\büberdies\b', r'(?i)\bes ist wichtig zu beachten\b', r'(?i)\bdaher\b',
                r'(?i)\bdemnach\b', r'(?i)\bjedoch\b', r'(?i)\binsgesamt\b',
                r'(?i)\bschlussfolgernd\b'
            ]
        }

    def detect_patterns(self, text: str, language: str) -> Dict:
        import re

        if language not in self.patterns:
            return {'pattern_count': 0, 'pattern_density': 0, 'patterns_found': []}

        patterns_found = []
        text_lower = text.lower()

        for pattern in self.patterns[language]:
            matches = re.findall(pattern, text_lower)
            if matches:
                patterns_found.append({
                    'pattern': pattern,
                    'count': len(matches),
                    'matches': matches[:3]
                })

        total_patterns = sum(p['count'] for p in patterns_found)
        word_count = len(text.split())
        pattern_density = total_patterns / (word_count + 1)

        return {
            'pattern_count': total_patterns,
            'pattern_density': pattern_density,
            'patterns_found': patterns_found[:5]
        }


class SurgicalEnsembleDetector:
    def __init__(self, use_gpu: bool = False):
        self.device = torch.device('cuda' if use_gpu and torch.cuda.is_available() else 'cpu')

        self.language_surgeon = LanguageSurgeon()
        self.embedding_surgeon = EmbeddingSurgeon()
        self.perplexity_surgeon = MultilingualPerplexitySurgeon()
        self.stylometric_surgeon = StylometricSurgeon()
        self.pattern_surgeon = AIPatternSurgeon()

        try:
            from HapppyEnd.web_searcher import WebSearcher
            self.web_searcher = WebSearcher()
        except ImportError:
            self.web_searcher = None

        self.load_detection_model()

    def load_detection_model(self):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        model_options = [
            'roberta-base-openai-detector',
            'microsoft/deberta-v3-base',
            'cointegrated/rubert-tiny',
        ]

        for model_name in model_options:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.model.to(self.device)
                self.model.eval()
                print(f"Neural model loaded: {model_name}")
                return
            except Exception:
                continue

        from sentence_transformers import SentenceTransformer
        self.fallback_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        print("Neural model: fallback embedding")

    def analyze(self, text: str, detailed: bool = False) -> Dict:
        lang_result = self.language_surgeon.detect_language(text)
        language = lang_result['language']
        lang_confidence = lang_result['confidence']

        style_result = self.stylometric_surgeon.analyze(text)
        pattern_result = self.pattern_surgeon.detect_patterns(text, language)
        nn_result = self.neural_analysis(text)

        if language in ['en', 'ru']:
            perplexity_result = self.perplexity_surgeon.calculate_perplexity(text, language)
            if perplexity_result['perplexity'] is None:
                perplexity_result = {'perplexity': None}
        else:
            perplexity_result = {'perplexity': None}

        web_result = {'similarity': 0.0, 'all_results': []}
        if self.web_searcher:
            try:
                web_result = self.web_searcher.search(text)
            except Exception:
                pass

        final_result = self.fuse_decisions(
            nn_result=nn_result,
            style_result=style_result,
            pattern_result=pattern_result,
            perplexity_result=perplexity_result,
            web_result=web_result
        )

        if detailed:
            final_result['language'] = language
            final_result['language_confidence'] = lang_confidence
            final_result['word_count'] = style_result.get('word_count', 0)
            final_result['perplexity_raw'] = perplexity_result.get('perplexity')
            final_result['pattern_count'] = pattern_result.get('pattern_count', 0)
            final_result['web_results'] = web_result.get('all_results', [])

        return final_result

    def neural_analysis(self, text: str) -> Dict:
        try:
            inputs = self.tokenizer(
                text,
                truncation=True,
                max_length=512,
                padding=True,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()[0]

            if len(probs) == 2:
                ai_prob = probs[1]
            else:
                ai_prob = probs[0]

            return {
                'raw_score': float(ai_prob),
                'ai_probability': float(ai_prob),
                'model_used': self.model.config.model_type
            }
        except Exception:
            embeddings = self.embedding_surgeon.embed(text)
            variance = np.var(embeddings)
            ai_prob = 1 / (1 + np.exp(-(variance - 0.5) * 10))

            return {
                'raw_score': float(ai_prob),
                'ai_probability': float(ai_prob),
                'model_used': 'fallback_embedding'
            }

    def fuse_decisions(self, **kwargs):
        if not kwargs:
            return {'ai_probability': 0.5, 'confidence': 0.1, 'verdict': 'Error'}

        nn_result = kwargs.get('nn_result', {})
        style_result = kwargs.get('style_result', {})
        pattern_result = kwargs.get('pattern_result', {})
        perplexity_result = kwargs.get('perplexity_result', {})
        web_result = kwargs.get('web_result', {})

        nn_score = nn_result.get('ai_probability', 0.5)

        ppl_score = 0.5
        if perplexity_result and perplexity_result.get('perplexity'):
            ppl = perplexity_result['perplexity']
            if ppl < 15:
                ppl_score = 0.9
            elif ppl < 25:
                ppl_score = 0.75
            elif ppl < 90:
                ppl_score = 0.6
            elif ppl < 120:
                ppl_score = 0.3
            else:
                ppl_score = 0.2

        style_score = 0.5
        if style_result:
            lex_div = style_result.get('lexical_diversity', 0.5)
            if lex_div < 0.3:
                style_score = 0.8
            elif lex_div < 0.5:
                style_score = 0.6
            elif lex_div < 0.7:
                style_score = 0.4
            else:
                style_score = 0.2

        pattern_score = 0.5
        if pattern_result:
            pattern_dens = pattern_result.get('pattern_density', 0)
            if pattern_dens > 0.08:
                pattern_score = 0.9
            elif pattern_dens > 0.05:
                pattern_score = 0.7
            elif pattern_dens > 0.02:
                pattern_score = 0.5
            else:
                pattern_score = 0.3

        web_score = web_result.get('similarity', 0.0)

        scores = [nn_score, ppl_score, style_score, pattern_score]
        weights = [0.4, 0.25, 0.2, 0.15]

        if not perplexity_result or not perplexity_result.get('perplexity'):
            weights[1] = 0
            total = sum(weights)
            if total > 0:
                weights = [w / total for w in weights]

        ai_prob = sum(s * w for s, w in zip(scores, weights))

        valid_scores = [s for s, w in zip(scores, weights) if w > 0]
        if len(valid_scores) >= 2:
            variance = np.var(valid_scores) if len(valid_scores) > 1 else 0
            confidence = max(0.3, 1.0 - variance * 4)
        else:
            confidence = 0.5

        word_count = style_result.get('word_count', 0)
        if word_count < 30:
            confidence *= 0.6
        elif word_count < 100:
            confidence *= 0.8

        ai_prob = min(0.99, max(0.01, ai_prob))
        confidence = min(0.95, max(0.1, confidence))

        return {
            'ai_probability': ai_prob,
            'confidence': confidence,
            'verdict': 'AI' if ai_prob > 0.5 else 'Human',
            'component_scores': {
                'neural_network': round(nn_score, 3),
                'perplexity': round(ppl_score, 3),
                'stylometric': round(style_score, 3),
                'patterns': round(pattern_score, 3),
                'web_search': round(web_score, 3)
            }
        }

    def analyze_batch(self, texts: List[str], batch_size: int = 32) -> List[Dict]:
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            for text in batch:
                if len(text.strip()) < 10:
                    results.append({
                        'ai_probability': 0.5,
                        'confidence': 0.1,
                        'verdict': 'Too short'
                    })
                    continue

                try:
                    result = self.analyze(text, detailed=False)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'ai_probability': 0.5,
                        'confidence': 0.1,
                        'verdict': 'Error',
                        'error': str(e)
                    })

        return results

    def clear_cache(self):
        import gc
        if hasattr(self.perplexity_surgeon, 'models'):
            for lang in self.perplexity_surgeon.models:
                self.perplexity_surgeon.models[lang] = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def export_report(self, result: Dict, format: str = 'json') -> str:
        if format == 'json':
            import json
            return json.dumps(result, indent=2, ensure_ascii=False)
        elif format == 'markdown':
            md = f"""
# AI Detection Report

## Verdict: {result.get('verdict', 'Unknown')}

### Probability: {result.get('ai_probability', 0):.1%}
### Confidence: {result.get('confidence', 0):.1%}

### Component Scores:
"""
            if 'component_scores' in result:
                for component, score in result['component_scores'].items():
                    if score != 'N/A':
                        md += f"- {component}: {score:.3f}\n"

            return md

        return str(result)