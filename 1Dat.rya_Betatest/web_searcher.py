# -*- coding:utf-8 -*-
import re
import webbrowser
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

REQUEST_TIMEOUT = 10
MAX_TEXT_LENGTH = 5000


class WebSearcher:
    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def search(self, text: str, num_results: int = 5) -> Dict:
        if len(text.strip()) < 50:
            return {'similarity': 0.0, 'all_results': [], 'error': 'Text too short'}

        search_query = ' '.join(text[:200].split())

        search_results = self._ddg_search(search_query, num_results)

        if not search_results:
            return {'similarity': 0.0, 'all_results': [], 'error': 'No search results'}

        pages = []
        for r in search_results:
            url = r.get('href')
            if not url:
                continue
            try:
                page_text = self._fetch_page(url)
                if page_text:
                    pages.append({'url': url, 'text': page_text})
            except Exception as e:
                print(f"Failed to fetch {url}: {e}")

        if not pages:
            return {'similarity': 0.0, 'all_results': [], 'error': 'No pages fetched'}

        return self._compare_results(text, pages)

    def _ddg_search(self, query: str, num_results: int) -> List[Dict]:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
                return results
        except Exception as e:
            print(f"DDGS search error: {e}")
            return []

    def _fetch_page(self, url: str) -> str:
        try:
            response = requests.get(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                return ""

            soup = BeautifulSoup(response.text, 'html.parser')

            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()

            main = soup.find('article') or soup.find('main') or soup.body
            if not main:
                return ""

            text = main.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text).strip()

            return text[:MAX_TEXT_LENGTH]
        except Exception:
            return ""

    def _compare_results(self, original: str, pages: List[Dict]) -> Dict:
        orig_clean = self._clean(original)
        all_results = []
        best_similarity = 0.0

        for page in pages:
            page_text = page.get('text', '')
            if not page_text:
                continue

            page_clean = self._clean(page_text)

            direct_match = self._find_direct_match(orig_clean, page_clean)

            if direct_match > 0:
                combined = direct_match
            else:
                ngram_sim = self._ngram_similarity(orig_clean, page_clean)
                combined = ngram_sim * 0.5

            all_results.append({
                'url': page.get('url', ''),
                'similarity': round(combined, 3),
                'snippet': page_text[:300]
            })

            if combined > best_similarity:
                best_similarity = combined

        all_results.sort(key=lambda x: x['similarity'], reverse=True)

        return {
            'similarity': round(best_similarity, 3),
            'all_results': all_results[:10]
        }

    def _find_direct_match(self, orig: str, page: str) -> float:
        if not orig or not page:
            return 0.0

        orig_squeezed = re.sub(r'[^a-zа-яё0-9]', '', orig)
        page_squeezed = re.sub(r'[^a-zа-яё0-9]', '', page)

        if orig_squeezed and len(orig_squeezed) > 20:
            if orig_squeezed in page_squeezed:
                return 1.0

        if orig in page:
            return 1.0

        orig_nospace = re.sub(r'\s+', '', orig)
        page_nospace = re.sub(r'\s+', '', page)
        if orig_nospace and orig_nospace in page_nospace:
            return 1.0

        sentences = [s.strip() for s in re.split(r'[.!?]\s+', orig) if len(s.strip()) > 20]

        if not sentences:
            return 0.0

        found = 0
        for sent in sentences:
            sent_nospace = re.sub(r'\s+', '', sent)
            sent_squeezed = re.sub(r'[^a-zа-яё0-9]', '', sent)
            if (sent in page
                or (sent_nospace and sent_nospace in page_nospace)
                or (sent_squeezed and sent_squeezed in page_squeezed)):
                found += 1

        sentence_ratio = found / len(sentences)

        orig_words = orig.split()
        if len(orig_words) >= 8:
            matches = 0
            windows = 0
            for i in range(0, len(orig_words) - 7, 2):
                window = ' '.join(orig_words[i:i+8])
                window_nospace = re.sub(r'\s+', '', window)
                window_squeezed = re.sub(r'[^a-zа-яё0-9]', '', window)
                windows += 1
                if (window in page
                    or (window_nospace and window_nospace in page_nospace)
                    or (window_squeezed and window_squeezed in page_squeezed)):
                    matches += 1

            if windows > 0:
                window_ratio = matches / windows
                return max(sentence_ratio, window_ratio)

        return sentence_ratio

    def _ngram_similarity(self, t1: str, t2: str, n: int = 4) -> float:
        def ngrams(t, size):
            return set(t[i:i+size] for i in range(len(t) - size + 1))

        ng1 = ngrams(t1[:500], n)
        ng2 = ngrams(t2[:500], n)

        if not ng1 or not ng2:
            return 0.0

        overlap = len(ng1 & ng2)
        total = len(ng1 | ng2)
        return overlap / total if total > 0 else 0.0

    def _clean(self, text: str) -> str:
        text = re.sub(r'<[^>]*>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.lower()
        text = re.sub(r'[^a-zа-яё0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


def show_web_links_window(web_results, lang, app=None):
    import dearpygui.dearpygui as dpg

    if dpg.does_item_exist("web_links_window"):
        dpg.delete_item("web_links_window")

    with dpg.window(
        label="Web Search Results",
        tag="web_links_window",
        width=500, height=400,
        pos=(200, 150)
    ):
        if not web_results:
            dpg.add_text("No results found")
            return

        for i, r in enumerate(web_results[:10]):
            url = r.get('url', '')
            snippet = r.get('snippet', '')
            sim = r.get('similarity', 0.0)
            sim_pct = int(sim * 100)

            if sim_pct >= 60:
                sim_color = (80, 200, 80, 255)
            elif sim_pct >= 30:
                sim_color = (220, 180, 60, 255)
            else:
                sim_color = (160, 160, 160, 255)

            dpg.add_text(f"[{sim_pct}%]", color=sim_color)

            if url:
                dpg.add_button(
                    label=f"{sim_pct}%",
                    small=True,
                    tag=f"web_btn_{i}",
                    callback=lambda s, a, u=url: webbrowser.open(u) if u else None
                )

            dpg.add_text(f"  {snippet[:120]}...", color=(180, 180, 180, 200))
            dpg.add_separator()