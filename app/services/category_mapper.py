"""
Category assignment for products without category information.
Uses hybrid approach: keyword-based rules + ML classification.
"""
import csv
import os
import re
from collections import defaultdict
from typing import Dict, Tuple, Optional

# Keyword-based category mapping rules
CATEGORY_KEYWORDS = {
    'Skincare': {
        'keywords': ['serum', 'cream', 'moisturizer', 'cleanser', 'toner', 'wash', 'gel',
                    'mask', 'oil', 'sunscreen', 'spf', 'treatment', 'lotion', 'essence',
                    'balm', 'exfoliat', 'peel', 'scrub', 'mist', 'spray', 'water'],
        'secondary': {
            'Moisturizers': ['cream', 'moisturizer', 'hydrat', 'lotion'],
            'Treatments': ['serum', 'treatment', 'acid', 'essence', 'booster', 'concentrate'],
            'Cleansers': ['cleanser', 'wash', 'foam', 'cleansing'],
            'Masks': ['mask', 'peel', 'sheet'],
            'Sun Care & Self Tanners': ['sunscreen', 'spf', 'sun'],
            'Facial Cleansing Brushes': ['brush', 'cleansing device'],
            'Eye Care': ['eye cream', 'eye serum', 'eye gel', 'under eye'],
            'Lip Balms & Treatments': ['lip balm', 'lip treatment', 'lip care']
        },
        'tertiary': {
            'Face Creams': ['face cream', 'facial cream'],
            'Face Serums': ['face serum', 'facial serum'],
            'Eye Creams': ['eye cream'],
            'Night Creams': ['night cream', 'sleeping'],
            'Face Wash': ['face wash', 'facial cleanser']
        }
    },
    'Makeup': {
        'keywords': ['lip', 'lipstick', 'gloss', 'foundation', 'concealer', 'powder',
                    'mascara', 'eyeshadow', 'eyeliner', 'blush', 'bronzer', 'highlighter',
                    'primer', 'setting', 'brow', 'eyebrow', 'lash', 'nail', 'polish'],
        'secondary': {
            'Lips': ['lip', 'lipstick', 'gloss', 'lip oil', 'lip stain', 'tint'],
            'Face': ['foundation', 'concealer', 'powder', 'primer', 'bb cream', 'cc cream'],
            'Eyes': ['eye', 'mascara', 'shadow', 'liner', 'brow', 'lash'],
            'Cheek': ['blush', 'bronzer', 'highlighter', 'contour'],
            'Nails': ['nail', 'polish', 'lacquer', 'manicure']
        },
        'tertiary': {
            'Lipstick': ['lipstick'],
            'Lip Gloss': ['lip gloss', 'gloss'],
            'Foundation': ['foundation'],
            'Concealer': ['concealer'],
            'Mascara': ['mascara']
        }
    },
    'Fragrance': {
        'keywords': ['perfume', 'eau de', 'cologne', 'fragrance', 'parfum', 'scent'],
        'secondary': {
            'Women': ['donna', 'femme', 'her', 'women', 'woman'],
            'Men': ['homme', 'him', 'men', 'pour homme'],
            'Value & Gift Sets': ['set', 'gift', 'duo', 'trio', 'mini']
        },
        'tertiary': {
            'Perfume': ['perfume', 'eau de parfum'],
            'Eau de Toilette': ['eau de toilette'],
            'Cologne': ['cologne']
        }
    },
    'Hair': {
        'keywords': ['shampoo', 'conditioner', 'hair oil', 'hair mask', 'hair spray',
                    'hair serum', 'scalp', 'styling'],
        'secondary': {
            'Shampoo & Conditioner': ['shampoo', 'conditioner'],
            'Hair Treatments': ['hair mask', 'hair treatment', 'hair serum'],
            'Styling Products': ['hair spray', 'gel', 'mousse', 'styling']
        }
    },
    'Bath & Body': {
        'keywords': ['body lotion', 'body cream', 'body oil', 'body wash', 'shower',
                    'bath', 'scrub', 'hand cream', 'foot'],
        'secondary': {
            'Body Moisturizers': ['body lotion', 'body cream', 'body butter'],
            'Cleansers': ['body wash', 'shower gel', 'soap'],
            'Hand Care': ['hand cream', 'hand lotion']
        }
    },
    'Tools & Brushes': {
        'keywords': ['brush', 'sponge', 'applicator', 'tool', 'device'],
        'secondary': {
            'Face Brushes': ['face brush', 'makeup brush'],
            'Skincare Tools': ['roller', 'gua sha', 'device']
        }
    }
}


class CategoryMapper:
    """Assigns categories to products using keyword rules and ML."""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.product_info_path = os.path.join(dataset_path, 'product_info.csv')
        self.product_item_path = os.path.join(dataset_path, 'product_item.csv')
        
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        if not text:
            return ''
        return text.lower().strip()
    
    def _match_keywords(self, product_name: str) -> Tuple[Optional[str], Optional[str], Optional[str], float]:
        """Match product name against keyword rules.
        
        Returns: (primary_category, secondary_category, tertiary_category, confidence)
        """
        name_lower = self._normalize_text(product_name)
        
        best_match = None
        best_confidence = 0.0
        
        for primary, data in CATEGORY_KEYWORDS.items():
            # Check primary keywords
            primary_score = 0
            for keyword in data['keywords']:
                if keyword in name_lower:
                    primary_score += 1
            
            if primary_score > 0:
                # Find best secondary category
                best_secondary = None
                best_secondary_score = 0
                
                for secondary, sec_keywords in data.get('secondary', {}).items():
                    sec_score = 0
                    for keyword in sec_keywords:
                        if keyword in name_lower:
                            sec_score += 2  # Higher weight for specific match
                    
                    if sec_score > best_secondary_score:
                        best_secondary_score = sec_score
                        best_secondary = secondary
                
                # Find best tertiary category
                best_tertiary = None
                best_tertiary_score = 0
                
                for tertiary, ter_keywords in data.get('tertiary', {}).items():
                    ter_score = 0
                    for keyword in ter_keywords:
                        if keyword in name_lower:
                            ter_score += 3  # Highest weight for most specific
                    
                    if ter_score > best_tertiary_score:
                        best_tertiary_score = ter_score
                        best_tertiary = tertiary
                
                total_score = primary_score + best_secondary_score + best_tertiary_score
                confidence = min(total_score / 10.0, 1.0)  # Normalize to 0-1
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = (primary, best_secondary, best_tertiary, confidence)
        
        if best_match:
            return best_match
        
        return None, None, None, 0.0
    
    def assign_categories_keywords(self) -> Dict[str, Dict]:
        """Assign categories using keyword-based rules."""
        # Load existing categories
        existing_categories = {}
        try:
            with open(self.product_info_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row.get('product_id')
                    if pid:
                        existing_categories[pid] = {
                            'primary_category': row.get('primary_category', ''),
                            'secondary_category': row.get('secondary_category', ''),
                            'tertiary_category': row.get('tertiary_category', '')
                        }
        except Exception as e:
            print(f"Error loading product_info: {e}")
        
        # Assign categories to items without them
        assignments = {}
        try:
            with open(self.product_item_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row.get('product_id')
                    if pid and pid not in existing_categories:
                        product_name = row.get('product_name', '')
                        primary, secondary, tertiary, confidence = self._match_keywords(product_name)
                        
                        if primary:
                            assignments[pid] = {
                                'product_id': pid,
                                'product_name': product_name,
                                'brand_name': row.get('brand_name', ''),
                                'primary_category': primary,
                                'secondary_category': secondary or '',
                                'tertiary_category': tertiary or '',
                                'confidence': confidence,
                                'method': 'keyword'
                            }
        except Exception as e:
            print(f"Error processing product_item: {e}")
        
        return assignments
    
    def train_ml_classifier(self):
        """Train ML classifier on existing categorized products."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.pipeline import Pipeline
        
        # Load training data from product_info
        train_data = []
        try:
            with open(self.product_info_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get('product_name', '')
                    primary = row.get('primary_category', '').strip()
                    secondary = row.get('secondary_category', '').strip()
                    
                    if name and primary:
                        train_data.append({
                            'text': name,
                            'primary': primary,
                            'secondary': secondary
                        })
        except Exception as e:
            print(f"Error loading training data: {e}")
            return None, None
        
        if len(train_data) < 10:
            print("Not enough training data")
            return None, None
        
        # Train primary category classifier
        texts = [d['text'] for d in train_data]
        primary_labels = [d['primary'] for d in train_data]
        
        primary_classifier = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
            ('clf', MultinomialNB())
        ])
        
        try:
            primary_classifier.fit(texts, primary_labels)
        except Exception as e:
            print(f"Error training primary classifier: {e}")
            return None, None
        
        # Train secondary category classifier
        secondary_train = [(d['text'], d['secondary']) for d in train_data if d['secondary']]
        if len(secondary_train) > 10:
            secondary_texts = [t for t, _ in secondary_train]
            secondary_labels = [l for _, l in secondary_train]
            
            secondary_classifier = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
                ('clf', MultinomialNB())
            ])
            
            try:
                secondary_classifier.fit(secondary_texts, secondary_labels)
            except Exception as e:
                print(f"Error training secondary classifier: {e}")
                secondary_classifier = None
        else:
            secondary_classifier = None
        
        return primary_classifier, secondary_classifier
    
    def assign_categories_ml(self, primary_clf, secondary_clf, keyword_assignments: Dict) -> Dict:
        """Assign categories using ML classifiers for items not covered by keywords."""
        if not primary_clf:
            return {}
        
        assignments = {}
        existing_categories = set()
        
        # Get existing categories
        try:
            with open(self.product_info_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row.get('product_id')
                    if pid:
                        existing_categories.add(pid)
        except Exception:
            pass
        
        # Classify items
        try:
            with open(self.product_item_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row.get('product_id')
                    if pid and pid not in existing_categories and pid not in keyword_assignments:
                        product_name = row.get('product_name', '')
                        
                        if not product_name:
                            continue
                        
                        # Predict primary
                        try:
                            primary_pred = primary_clf.predict([product_name])[0]
                            primary_proba = max(primary_clf.predict_proba([product_name])[0])
                            
                            # Predict secondary
                            secondary_pred = ''
                            if secondary_clf:
                                try:
                                    secondary_pred = secondary_clf.predict([product_name])[0]
                                except Exception:
                                    pass
                            
                            assignments[pid] = {
                                'product_id': pid,
                                'product_name': product_name,
                                'brand_name': row.get('brand_name', ''),
                                'primary_category': primary_pred,
                                'secondary_category': secondary_pred,
                                'tertiary_category': '',
                                'confidence': primary_proba,
                                'method': 'ml'
                            }
                        except Exception as e:
                            continue
        except Exception as e:
            print(f"Error in ML classification: {e}")
        
        return assignments


def run_categorization(dataset_path: str, output_path: str):
    """Run full categorization process and save results."""
    print("🚀 Starting hybrid categorization process...\n")
    
    mapper = CategoryMapper(dataset_path)
    
    # Phase 1: Keyword-based
    print("📋 Phase 1: Keyword-based categorization...")
    keyword_assignments = mapper.assign_categories_keywords()
    print(f"   ✅ Assigned {len(keyword_assignments)} items using keywords\n")
    
    # Phase 2: ML-based
    print("🤖 Phase 2: Training ML classifiers...")
    primary_clf, secondary_clf = mapper.train_ml_classifier()
    
    ml_assignments = {}
    if primary_clf:
        print("   ✅ Classifiers trained successfully")
        print("   📊 Classifying remaining items...")
        ml_assignments = mapper.assign_categories_ml(primary_clf, secondary_clf, keyword_assignments)
        print(f"   ✅ Assigned {len(ml_assignments)} items using ML\n")
    else:
        print("   ⚠️  ML training failed, using keywords only\n")
    
    # Combine results
    all_assignments = {**keyword_assignments, **ml_assignments}
    
    print(f"📈 Total new assignments: {len(all_assignments)}")
    print(f"   - Keyword-based: {len(keyword_assignments)}")
    print(f"   - ML-based: {len(ml_assignments)}\n")
    
    # Save to CSV
    if all_assignments:
        print(f"💾 Saving to {output_path}...")
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['product_id', 'product_name', 'brand_name', 
                         'primary_category', 'secondary_category', 'tertiary_category',
                         'confidence', 'method']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for assignment in all_assignments.values():
                writer.writerow(assignment)
        
        print(f"✅ Categorization complete! Saved to {output_path}\n")
        
        # Print statistics
        by_method = defaultdict(int)
        by_primary = defaultdict(int)
        for a in all_assignments.values():
            by_method[a['method']] += 1
            by_primary[a['primary_category']] += 1
        
        print("📊 Statistics:")
        print(f"   By method:")
        for method, count in sorted(by_method.items()):
            print(f"      {method}: {count}")
        
        print(f"\n   By primary category:")
        for cat, count in sorted(by_primary.items(), key=lambda x: x[1], reverse=True):
            print(f"      {cat}: {count}")
    
    return all_assignments
