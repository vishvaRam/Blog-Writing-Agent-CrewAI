"""
Content Tools for CrewAI Blog Automation
Tools for content structuring, SEO optimization, and readability analysis
"""

import re
import json
from typing import Dict, List, Any, Optional
from crewai.tools import BaseTool
import math


class ContentStructuringTool(BaseTool):
    name: str = "Content Structuring Tool"
    description: str = "Structure and format blog content for optimal readability and engagement"
    
    def _run(self, content: str, title: str = "", target_read_time: int = 8) -> str:
        """
        Structure and analyze blog content
        
        Args:
            content: Raw blog content
            title: Blog post title
            target_read_time: Target reading time in minutes
        """
        try:
            analysis = self._analyze_content_structure(content)
            suggestions = self._generate_structure_suggestions(content, target_read_time)
            formatted_content = self._apply_formatting_improvements(content)
            
            return json.dumps({
                'original_content': content,
                'formatted_content': formatted_content,
                'title': title,
                'structure_analysis': analysis,
                'improvement_suggestions': suggestions,
                'target_read_time_minutes': target_read_time,
                'current_read_time_minutes': analysis.get('estimated_read_time', 0)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'error': f"Error structuring content: {str(e)}",
                'original_content': content[:500] + '...' if len(content) > 500 else content
            })
    
    def _analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """Analyze content structure and readability metrics"""
        
        # Basic metrics
        word_count = len(content.split())
        char_count = len(content)
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        
        # Reading time estimation (average 200 words per minute)
        estimated_read_time = math.ceil(word_count / 200)
        
        # Heading analysis
        headings = {
            'h1': len(re.findall(r'^# .+', content, re.MULTILINE)),
            'h2': len(re.findall(r'^## .+', content, re.MULTILINE)),
            'h3': len(re.findall(r'^### .+', content, re.MULTILINE)),
            'h4': len(re.findall(r'^#### .+', content, re.MULTILINE))
        }
        
        # Sentence analysis
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Paragraph analysis
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        
        return {
            'word_count': word_count,
            'character_count': char_count,
            'paragraph_count': paragraph_count,
            'sentence_count': len(sentences),
            'estimated_read_time': estimated_read_time,
            'headings': headings,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_paragraph_length': round(avg_paragraph_length, 1),
            'readability_score': self._calculate_readability_score(sentences, word_count)
        }
    
    def _calculate_readability_score(self, sentences: List[str], word_count: int) -> Dict[str, Any]:
        """Calculate readability metrics"""
        if not sentences or word_count == 0:
            return {'score': 0, 'level': 'unreadable'}
        
        # Simplified Flesch Reading Ease approximation
        avg_sentence_length = word_count / len(sentences)
        
        # Estimate syllables (rough approximation)
        syllable_count = 0
        for sentence in sentences:
            words = sentence.split()
            for word in words:
                # Simple syllable estimation
                word = word.lower().strip('.,!?";')
                syllable_count += max(1, len(re.findall(r'[aeiouyAEIOUY]', word)))
        
        avg_syllables_per_word = syllable_count / word_count if word_count > 0 else 0
        
        # Simplified Flesch Reading Ease Score
        reading_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        reading_ease = max(0, min(100, reading_ease))  # Clamp between 0-100
        
        # Determine reading level
        if reading_ease >= 90:
            level = "very easy"
        elif reading_ease >= 80:
            level = "easy"
        elif reading_ease >= 70:
            level = "fairly easy"
        elif reading_ease >= 60:
            level = "standard"
        elif reading_ease >= 50:
            level = "fairly difficult"
        elif reading_ease >= 30:
            level = "difficult"
        else:
            level = "very difficult"
        
        return {
            'score': round(reading_ease, 1),
            'level': level,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_syllables_per_word': round(avg_syllables_per_word, 1)
        }
    
    def _generate_structure_suggestions(self, content: str, target_read_time: int) -> List[str]:
        """Generate suggestions for improving content structure"""
        suggestions = []
        analysis = self._analyze_content_structure(content)
        
        # Word count suggestions
        current_read_time = analysis['estimated_read_time']
        target_word_count = target_read_time * 200
        current_word_count = analysis['word_count']
        
        if current_word_count < target_word_count * 0.8:
            suggestions.append(f"Content is too short ({current_word_count} words). Target: {target_word_count} words for {target_read_time}-minute read.")
        elif current_word_count > target_word_count * 1.2:
            suggestions.append(f"Content might be too long ({current_word_count} words). Consider condensing for {target_read_time}-minute read.")
        
        # Heading structure suggestions
        headings = analysis['headings']
        if headings['h1'] == 0:
            suggestions.append("Add a main H1 heading for better structure.")
        elif headings['h1'] > 1:
            suggestions.append("Consider using only one H1 heading per post.")
        
        if headings['h2'] < 3:
            suggestions.append("Add more H2 sections (3-6 recommended) for better content organization.")
        
        # Paragraph suggestions
        if analysis['avg_paragraph_length'] > 100:
            suggestions.append("Break up long paragraphs (current average: {:.1f} words). Aim for 50-80 words per paragraph.".format(analysis['avg_paragraph_length']))
        
        # Sentence length suggestions
        if analysis['avg_sentence_length'] > 25:
            suggestions.append("Consider shorter sentences (current average: {:.1f} words). Aim for 15-20 words per sentence.".format(analysis['avg_sentence_length']))
        
        # Readability suggestions
        readability = analysis['readability_score']
        if readability['score'] < 50:
            suggestions.append(f"Content readability is {readability['level']} (score: {readability['score']}). Consider simpler language and shorter sentences.")
        
        return suggestions
    
    def _apply_formatting_improvements(self, content: str) -> str:
        """Apply basic formatting improvements to content"""
        
        # Fix common formatting issues
        improved_content = content
        
        # Ensure proper spacing around headings
        improved_content = re.sub(r'\n(#+\s)', r'\n\n\1', improved_content)
        improved_content = re.sub(r'(#+\s.+)\n([^\n])', r'\1\n\n\2', improved_content)
        
        # Fix multiple consecutive newlines
        improved_content = re.sub(r'\n{3,}', '\n\n', improved_content)
        
        # Ensure proper spacing around list items
        improved_content = re.sub(r'\n(\*|\-|\d+\.)\s', r'\n\n\1 ', improved_content)
        
        # Fix spacing around emphasis
        improved_content = re.sub(r'(\*\*[^*]+\*\*)', r' \1 ', improved_content)
        improved_content = re.sub(r'\s+', ' ', improved_content)  # Clean up extra spaces
        
        return improved_content.strip()


class SEOOptimizationTool(BaseTool):
    name: str = "SEO Optimization Tool"
    description: str = "Analyze and optimize content for search engines with keyword analysis and meta tag generation"
    
    def _run(self, content: str, title: str, target_keywords: str = "", focus_keyword: str = "") -> str:
        """
        Analyze and optimize content for SEO
        
        Args:
            content: Blog post content
            title: Blog post title
            target_keywords: Comma-separated target keywords
            focus_keyword: Primary focus keyword
        """
        try:
            keywords_list = [k.strip().lower() for k in target_keywords.split(',') if k.strip()]
            if focus_keyword:
                focus_keyword = focus_keyword.strip().lower()
            
            seo_analysis = self._analyze_seo_factors(content, title, keywords_list, focus_keyword)
            meta_tags = self._generate_meta_tags(content, title, focus_keyword)
            optimizations = self._suggest_optimizations(seo_analysis)
            
            return json.dumps({
                'title': title,
                'focus_keyword': focus_keyword,
                'target_keywords': keywords_list,
                'seo_analysis': seo_analysis,
                'meta_tags': meta_tags,
                'optimization_suggestions': optimizations,
                'seo_score': self._calculate_seo_score(seo_analysis)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'error': f"Error in SEO optimization: {str(e)}",
                'title': title
            })
    
    def _analyze_seo_factors(self, content: str, title: str, keywords: List[str], focus_keyword: str) -> Dict[str, Any]:
        """Analyze various SEO factors"""
        
        content_lower = content.lower()
        title_lower = title.lower()
        word_count = len(content.split())
        
        analysis = {
            'word_count': word_count,
            'title_length': len(title),
            'keyword_analysis': {}
        }
        
        # Analyze focus keyword
        if focus_keyword:
            focus_in_title = focus_keyword in title_lower
            focus_density = content_lower.count(focus_keyword) / word_count * 100 if word_count > 0 else 0
            focus_in_first_paragraph = focus_keyword in content_lower[:200]
            
            analysis['keyword_analysis'][focus_keyword] = {
                'in_title': focus_in_title,
                'density_percent': round(focus_density, 2),
                'count': content_lower.count(focus_keyword),
                'in_first_paragraph': focus_in_first_paragraph,
                'is_focus_keyword': True
            }
        
        # Analyze target keywords
        for keyword in keywords:
            if keyword != focus_keyword:  # Avoid duplicate analysis
                in_title = keyword in title_lower
                density = content_lower.count(keyword) / word_count * 100 if word_count > 0 else 0
                
                analysis['keyword_analysis'][keyword] = {
                    'in_title': in_title,
                    'density_percent': round(density, 2),
                    'count': content_lower.count(keyword),
                    'is_focus_keyword': False
                }
        
        # Heading analysis
        h1_count = len(re.findall(r'^# .+', content, re.MULTILINE))
        h2_count = len(re.findall(r'^## .+', content, re.MULTILINE))
        h3_count = len(re.findall(r'^### .+', content, re.MULTILINE))
        
        analysis['headings'] = {
            'h1_count': h1_count,
            'h2_count': h2_count,
            'h3_count': h3_count,
            'proper_hierarchy': h1_count == 1 and h2_count >= 2
        }
        
        # Content structure analysis
        analysis['content_structure'] = {
            'has_introduction': len(content) > 300,  # Assumes intro if content is substantial
            'has_conclusion': 'conclusion' in content_lower or 'summary' in content_lower,
            'internal_links': len(re.findall(r'\[([^\]]+)\]\([^)]+\)', content)),
            'external_links': len(re.findall(r'\[([^\]]+)\]\(http[s]?://[^)]+\)', content)),
            'images_mentioned': content.count('![') + content.count('[image') + content.count('[Image')
        }
        
        return analysis
    
    def _generate_meta_tags(self, content: str, title: str, focus_keyword: str = "") -> Dict[str, str]:
        """Generate SEO meta tags"""
        
        # Generate meta description from first paragraph or summary
        first_paragraph = content.split('\n\n')[0] if '\n\n' in content else content[:300]
        # Remove markdown formatting
        clean_paragraph = re.sub(r'[#*`\[\]()]', '', first_paragraph)
        
        # Create meta description (150-160 characters)
        meta_description = clean_paragraph[:150].strip()
        if len(clean_paragraph) > 150:
            # Try to end at a word boundary
            last_space = meta_description.rfind(' ')
            if last_space > 120:
                meta_description = meta_description[:last_space] + '...'
        
        # Generate title tag (include focus keyword if provided)
        title_tag = title
        if focus_keyword and focus_keyword not in title.lower():
            title_tag = f"{title} - {focus_keyword.title()}"
        
        # Ensure title is within optimal length (50-60 characters)
        if len(title_tag) > 60:
            title_tag = title[:57] + '...'
        
        return {
            'title': title_tag,
            'meta_description': meta_description,
            'og_title': title,
            'og_description': meta_description,
            'twitter_title': title,
            'twitter_description': meta_description
        }
    
    def _suggest_optimizations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate SEO optimization suggestions"""
        suggestions = []
        
        # Word count suggestions
        word_count = analysis['word_count']
        if word_count < 1000:
            suggestions.append(f"Content is short ({word_count} words). Consider expanding to 1,500+ words for better SEO.")
        elif word_count > 3000:
            suggestions.append(f"Content is very long ({word_count} words). Consider breaking into multiple posts or adding subheadings.")
        
        # Title length suggestions
        title_length = analysis['title_length']
        if title_length < 30:
            suggestions.append(f"Title is short ({title_length} characters). Optimize for 50-60 characters.")
        elif title_length > 70:
            suggestions.append(f"Title is long ({title_length} characters). Consider shortening to under 60 characters.")
        
        # Keyword optimization
        for keyword, data in analysis['keyword_analysis'].items():
            if data['is_focus_keyword']:
                if not data['in_title']:
                    suggestions.append(f"Focus keyword '{keyword}' not found in title. Consider adding it.")
                if data['density_percent'] < 0.5:
                    suggestions.append(f"Focus keyword '{keyword}' density is low ({data['density_percent']}%). Aim for 0.5-2%.")
                elif data['density_percent'] > 3:
                    suggestions.append(f"Focus keyword '{keyword}' density is high ({data['density_percent']}%). Consider reducing to avoid over-optimization.")
                if not data['in_first_paragraph']:
                    suggestions.append(f"Focus keyword '{keyword}' not found in first paragraph. Consider adding it early.")
        
        # Heading structure
        headings = analysis['headings']
        if headings['h1_count'] == 0:
            suggestions.append("Add an H1 heading for better structure.")
        elif headings['h1_count'] > 1:
            suggestions.append("Use only one H1 heading per post.")
        
        if headings['h2_count'] < 2:
            suggestions.append("Add more H2 headings (2-6 recommended) to improve content structure.")
        
        # Content structure
        structure = analysis['content_structure']
        if structure['internal_links'] == 0:
            suggestions.append("Add internal links to other relevant content.")
        
        if structure['images_mentioned'] == 0:
            suggestions.append("Add images to improve engagement and SEO.")
        
        return suggestions
    
    def _calculate_seo_score(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall SEO score"""
        score = 0
        max_score = 100
        
        # Word count score (15 points)
        word_count = analysis['word_count']
        if 1500 <= word_count <= 2500:
            score += 15
        elif 1000 <= word_count < 1500 or 2500 < word_count <= 3000:
            score += 10
        elif 800 <= word_count < 1000:
            score += 5
        
        # Title length score (10 points)
        title_length = analysis['title_length']
        if 40 <= title_length <= 60:
            score += 10
        elif 30 <= title_length < 40 or 60 < title_length <= 70:
            score += 7
        
        # Keyword optimization score (25 points)
        keyword_score = 0
        for keyword, data in analysis['keyword_analysis'].items():
            if data['is_focus_keyword']:
                if data['in_title']:
                    keyword_score += 8
                if 0.5 <= data['density_percent'] <= 2:
                    keyword_score += 10
                if data['in_first_paragraph']:
                    keyword_score += 7
                break  # Only score focus keyword
        score += min(25, keyword_score)
        
        # Heading structure score (15 points)
        headings = analysis['headings']
        if headings['proper_hierarchy']:
            score += 15
        elif headings['h1_count'] == 1:
            score += 10
        elif headings['h2_count'] >= 2:
            score += 8
        
        # Content structure score (25 points)
        structure = analysis['content_structure']
        if structure['has_introduction']:
            score += 5
        if structure['has_conclusion']:
            score += 5
        if structure['internal_links'] > 0:
            score += 8
        if structure['images_mentioned'] > 0:
            score += 7
        
        # Additional points (10 points)
        if structure['external_links'] > 0:
            score += 5
        if headings['h3_count'] > 0:
            score += 5
        
        # Determine grade
        if score >= 80:
            grade = "A"
        elif score >= 70:
            grade = "B"
        elif score >= 60:
            grade = "C"
        elif score >= 50:
            grade = "D"
        else:
            grade = "F"
        
        return {
            'score': min(max_score, score),
            'max_score': max_score,
            'grade': grade,
            'percentage': round((min(max_score, score) / max_score) * 100, 1)
        }