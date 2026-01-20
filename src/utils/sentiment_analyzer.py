"""
Review Sentiment Analyzer
Analyzes product reviews to extract sentiment and key pros/cons
"""

from typing import List, Tuple
from collections import Counter
import re

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

from src.models.product import ReviewSentiment


class SentimentAnalyzer:
    """Analyze product review sentiment"""
    
    def __init__(self):
        if VADER_AVAILABLE:
            self.analyzer = SentimentIntensityAnalyzer()
        else:
            self.analyzer = None
            print("⚠️  VADER not available, using simple sentiment")
    
    def analyze_reviews(
        self,
        reviews: List[str],
        min_reviews: int = 5
    ) -> ReviewSentiment:
        """
        Analyze a list of reviews and return sentiment
        
        Args:
            reviews: List of review texts
            min_reviews: Minimum reviews needed for analysis
            
        Returns:
            ReviewSentiment object
        """
        if len(reviews) < min_reviews:
            # Not enough reviews for meaningful analysis
            return ReviewSentiment(
                positive=50,
                neutral=30,
                negative=20,
                top_pros=[],
                top_cons=[],
                sample_reviews=reviews[:3]
            )
        
        # Analyze sentiment
        sentiments = []
        for review in reviews:
            sentiment = self._analyze_single_review(review)
            sentiments.append(sentiment)
        
        # Calculate percentages
        positive_count = sum(1 for s in sentiments if s == 'positive')
        negative_count = sum(1 for s in sentiments if s == 'negative')
        neutral_count = len(sentiments) - positive_count - negative_count
        
        total = len(sentiments)
        positive_pct = int((positive_count / total) * 100)
        negative_pct = int((negative_count / total) * 100)
        neutral_pct = 100 - positive_pct - negative_pct
        
        # Extract pros and cons
        pros, cons = self._extract_pros_cons(reviews)
        
        # Get sample reviews
        sample_reviews = self._get_sample_reviews(reviews, sentiments)
        
        return ReviewSentiment(
            positive=positive_pct,
            neutral=neutral_pct,
            negative=negative_pct,
            top_pros=pros[:10],
            top_cons=cons[:10],
            sample_reviews=sample_reviews
        )
    
    def _analyze_single_review(self, review: str) -> str:
        """Analyze single review sentiment"""
        if self.analyzer:
            # Use VADER
            scores = self.analyzer.polarity_scores(review)
            compound = scores['compound']
            
            if compound >= 0.05:
                return 'positive'
            elif compound <= -0.05:
                return 'negative'
            else:
                return 'neutral'
        else:
            # Simple keyword-based sentiment
            positive_words = ['great', 'excellent', 'amazing', 'love', 'perfect', 'best', 'awesome', 'good', 'nice', 'fantastic']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'poor', 'disappointing', 'waste', 'broken', 'defective']
            
            review_lower = review.lower()
            positive_score = sum(1 for word in positive_words if word in review_lower)
            negative_score = sum(1 for word in negative_words if word in review_lower)
            
            if positive_score > negative_score:
                return 'positive'
            elif negative_score > positive_score:
                return 'negative'
            else:
                return 'neutral'
    
    def _extract_pros_cons(
        self,
        reviews: List[str]
    ) -> Tuple[List[str], List[str]]:
        """Extract common pros and cons from reviews"""
        
        # Common positive phrases
        positive_patterns = [
            r'great (\w+)',
            r'excellent (\w+)',
            r'love the (\w+)',
            r'perfect (\w+)',
            r'amazing (\w+)',
            r'good (\w+)',
            r'fast (\w+)',
            r'easy to (\w+)',
        ]
        
        # Common negative phrases
        negative_patterns = [
            r'poor (\w+)',
            r'terrible (\w+)',
            r'bad (\w+)',
            r'disappointing (\w+)',
            r'slow (\w+)',
            r'difficult to (\w+)',
            r'does not (\w+)',
            r'doesn\'t (\w+)',
        ]
        
        pros = []
        cons = []
        
        for review in reviews:
            review_lower = review.lower()
            
            # Extract pros
            for pattern in positive_patterns:
                matches = re.findall(pattern, review_lower)
                pros.extend(matches)
            
            # Extract cons
            for pattern in negative_patterns:
                matches = re.findall(pattern, review_lower)
                cons.extend(matches)
        
        # Count and get top items
        if pros:
            pro_counter = Counter(pros)
            top_pros = [item for item, count in pro_counter.most_common(10)]
        else:
            top_pros = []
        
        if cons:
            con_counter = Counter(cons)
            top_cons = [item for item, count in con_counter.most_common(10)]
        else:
            top_cons = []
        
        return top_pros, top_cons
    
    def _get_sample_reviews(
        self,
        reviews: List[str],
        sentiments: List[str]
    ) -> List[str]:
        """Get representative sample reviews"""
        samples = []
        
        # Get one positive, one neutral, one negative
        for sentiment_type in ['positive', 'neutral', 'negative']:
            for review, sentiment in zip(reviews, sentiments):
                if sentiment == sentiment_type and review not in samples:
                    samples.append(review[:200])  # Truncate long reviews
                    break
        
        # Fill up to 5 samples
        for review in reviews:
            if review[:200] not in samples and len(samples) < 5:
                samples.append(review[:200])
        
        return samples


# Convenience function
def analyze_product_reviews(reviews: List[str]) -> ReviewSentiment:
    """Quick function to analyze reviews"""
    analyzer = SentimentAnalyzer()
    return analyzer.analyze_reviews(reviews)


# CLI for testing
if __name__ == "__main__":
    # Test reviews
    test_reviews = [
        "This product is amazing! Great quality and fast shipping.",
        "Perfect for my needs. Love the design and features.",
        "Terrible product. Broke after 2 days. Very disappointed.",
        "It's okay. Nothing special but gets the job done.",
        "Excellent value for money. Highly recommend!",
        "Poor quality. Not worth the price at all.",
        "Good product overall. Fast delivery and easy to use.",
    ]
    
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze_reviews(test_reviews)
    
    print("🎯 Review Sentiment Analysis")
    print("=" * 50)
    print(f"Positive: {result.positive}%")
    print(f"Neutral:  {result.neutral}%")
    print(f"Negative: {result.negative}%")
    print(f"\nTop Pros: {', '.join(result.top_pros[:5])}")
    print(f"Top Cons: {', '.join(result.top_cons[:5])}")
    print(f"\nSample Reviews:")
    for i, review in enumerate(result.sample_reviews, 1):
        print(f"{i}. {review}")
