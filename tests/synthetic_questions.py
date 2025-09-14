"""
Synthetic Question Generator for FACT System Testing

Generates comprehensive test questions covering all aspects of contractor
licensing knowledge with varying complexity levels and realistic scenarios.
"""

import random
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import itertools

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class TestQuestion:
    """Test question with metadata for evaluation"""
    id: str
    text: str
    category: str
    state: Optional[str] = None
    expected_keywords: List[str] = None
    difficulty: str = "medium"  # easy, medium, hard
    question_type: str = "general"  # general, specific, comparison, scenario
    expected_response_type: str = "informational"  # informational, procedural, numerical
    
    def __post_init__(self):
        if self.expected_keywords is None:
            self.expected_keywords = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class QuestionTemplate:
    """Template for generating questions with variations"""
    
    def __init__(self, template: str, variables: Dict[str, List[str]], 
                 category: str, difficulty: str = "medium",
                 expected_keywords: List[str] = None):
        self.template = template
        self.variables = variables
        self.category = category
        self.difficulty = difficulty
        self.expected_keywords = expected_keywords or []
    
    def generate_questions(self, count: int = 5) -> List[TestQuestion]:
        """Generate questions from this template"""
        questions = []
        
        # Generate all possible combinations (limited by count)
        var_names = list(self.variables.keys())
        var_combinations = list(itertools.product(*[self.variables[name] for name in var_names]))
        
        # Randomly sample combinations if we have more than needed
        if len(var_combinations) > count:
            var_combinations = random.sample(var_combinations, count)
        
        for i, combination in enumerate(var_combinations[:count]):
            # Create variable substitution dict
            substitutions = dict(zip(var_names, combination))
            
            # Generate question text
            question_text = self.template.format(**substitutions)
            
            # Extract state if present in substitutions
            state = substitutions.get('state') or substitutions.get('location')
            
            # Create question
            question = TestQuestion(
                id=f"{self.category}_{i+1}_{random.randint(1000, 9999)}",
                text=question_text,
                category=self.category,
                state=state,
                difficulty=self.difficulty,
                expected_keywords=self.expected_keywords.copy()
            )
            
            questions.append(question)
        
        return questions


class SyntheticQuestionGenerator:
    """
    Main class for generating comprehensive test questions.
    
    Creates realistic questions covering all aspects of contractor licensing
    with appropriate difficulty levels and expected response characteristics.
    """
    
    def __init__(self):
        self.states = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]
        
        self.state_names = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
            'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
            'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
            'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming'
        }
        
        self.contractor_types = [
            'general contractor', 'electrical contractor', 'plumbing contractor',
            'HVAC contractor', 'roofing contractor', 'concrete contractor',
            'framing contractor', 'painting contractor', 'flooring contractor',
            'landscaping contractor', 'specialty contractor'
        ]
        
        self.question_templates = self._create_question_templates()
    
    def _create_question_templates(self) -> Dict[str, List[QuestionTemplate]]:
        """Create comprehensive question templates for all categories"""
        templates = {}
        
        # 1. State Licensing Requirements
        templates['state_licensing_requirements'] = [
            QuestionTemplate(
                "What are the requirements for a {contractor_type} license in {state}?",
                {
                    'contractor_type': self.contractor_types,
                    'state': self.states
                },
                category='state_licensing_requirements',
                difficulty='easy',
                expected_keywords=['requirements', 'license', 'experience', 'exam']
            ),
            QuestionTemplate(
                "How do I get licensed as a contractor in {state_name}?",
                {
                    'state_name': list(self.state_names.values())
                },
                category='state_licensing_requirements',
                difficulty='easy',
                expected_keywords=['license', 'application', 'requirements']
            ),
            QuestionTemplate(
                "What experience is required for a {state} contractor license?",
                {
                    'state': self.states
                },
                category='state_licensing_requirements',
                difficulty='medium',
                expected_keywords=['experience', 'years', 'requirements']
            ),
            QuestionTemplate(
                "Does {state} require a surety bond for contractors, and if so, how much?",
                {
                    'state': self.states
                },
                category='state_licensing_requirements',
                difficulty='medium',
                expected_keywords=['bond', 'surety', 'amount', 'required']
            ),
            QuestionTemplate(
                "What's the difference between a Class A and Class B contractor license in {state}?",
                {
                    'state': self.states
                },
                category='state_licensing_requirements',
                difficulty='hard',
                expected_keywords=['Class A', 'Class B', 'difference', 'license']
            )
        ]
        
        # 2. Exam Preparation & Testing
        templates['exam_preparation_testing'] = [
            QuestionTemplate(
                "How many questions are on the {state} contractor exam?",
                {
                    'state': self.states
                },
                category='exam_preparation_testing',
                difficulty='easy',
                expected_keywords=['questions', 'exam', 'test']
            ),
            QuestionTemplate(
                "What's the passing score for the contractor exam in {state}?",
                {
                    'state': self.states
                },
                category='exam_preparation_testing',
                difficulty='easy',
                expected_keywords=['passing', 'score', 'exam', 'percentage']
            ),
            QuestionTemplate(
                "How should I study for the {state} contractor business and law exam?",
                {
                    'state': self.states
                },
                category='exam_preparation_testing',
                difficulty='medium',
                expected_keywords=['study', 'business', 'law', 'exam', 'preparation']
            ),
            QuestionTemplate(
                "What happens if I fail the contractor exam in {state}?",
                {
                    'state': self.states
                },
                category='exam_preparation_testing',
                difficulty='medium',
                expected_keywords=['fail', 'retake', 'exam', 'retest']
            ),
            QuestionTemplate(
                "Are there practice tests available for the {state} {contractor_type} exam?",
                {
                    'state': self.states,
                    'contractor_type': self.contractor_types
                },
                category='exam_preparation_testing',
                difficulty='medium',
                expected_keywords=['practice', 'test', 'exam', 'study']
            )
        ]
        
        # 3. Qualifier Network Programs
        templates['qualifier_network_programs'] = [
            QuestionTemplate(
                "What is a qualifier network program for contractors?",
                {},
                category='qualifier_network_programs',
                difficulty='easy',
                expected_keywords=['qualifier', 'network', 'program', 'contractors']
            ),
            QuestionTemplate(
                "How can I find a qualifier to sponsor my contractor license?",
                {},
                category='qualifier_network_programs',
                difficulty='medium',
                expected_keywords=['qualifier', 'sponsor', 'license', 'find']
            ),
            QuestionTemplate(
                "What are the benefits of joining a contractor network program?",
                {},
                category='qualifier_network_programs',
                difficulty='medium',
                expected_keywords=['benefits', 'network', 'program', 'contractors']
            ),
            QuestionTemplate(
                "How much does it cost to join a qualifier network?",
                {},
                category='qualifier_network_programs',
                difficulty='medium',
                expected_keywords=['cost', 'qualifier', 'network', 'join']
            ),
            QuestionTemplate(
                "Can I get leads through a contractor network program?",
                {},
                category='qualifier_network_programs',
                difficulty='hard',
                expected_keywords=['leads', 'network', 'program', 'business']
            )
        ]
        
        # 4. Business Formation & Operations
        templates['business_formation_operations'] = [
            QuestionTemplate(
                "Should I form an LLC or corporation for my contracting business?",
                {},
                category='business_formation_operations',
                difficulty='medium',
                expected_keywords=['LLC', 'corporation', 'business', 'formation']
            ),
            QuestionTemplate(
                "What business licenses do I need besides my contractor license?",
                {},
                category='business_formation_operations',
                difficulty='medium',
                expected_keywords=['business', 'licenses', 'contractor', 'required']
            ),
            QuestionTemplate(
                "How do I set up workers compensation insurance for my contracting business?",
                {},
                category='business_formation_operations',
                difficulty='hard',
                expected_keywords=['workers compensation', 'insurance', 'business']
            ),
            QuestionTemplate(
                "What accounting software is best for contractors?",
                {},
                category='business_formation_operations',
                difficulty='medium',
                expected_keywords=['accounting', 'software', 'contractors']
            ),
            QuestionTemplate(
                "Do I need a separate business bank account for my contracting business?",
                {},
                category='business_formation_operations',
                difficulty='easy',
                expected_keywords=['business', 'bank', 'account', 'separate']
            )
        ]
        
        # 5. Insurance & Bonding
        templates['insurance_bonding'] = [
            QuestionTemplate(
                "What types of insurance do contractors need?",
                {},
                category='insurance_bonding',
                difficulty='easy',
                expected_keywords=['insurance', 'contractors', 'types', 'liability']
            ),
            QuestionTemplate(
                "How much does general liability insurance cost for contractors?",
                {},
                category='insurance_bonding',
                difficulty='medium',
                expected_keywords=['liability', 'insurance', 'cost', 'contractors']
            ),
            QuestionTemplate(
                "What's the difference between a surety bond and insurance?",
                {},
                category='insurance_bonding',
                difficulty='hard',
                expected_keywords=['surety', 'bond', 'insurance', 'difference']
            ),
            QuestionTemplate(
                "How much does a {amount} surety bond cost?",
                {
                    'amount': ['$10,000', '$15,000', '$25,000', '$50,000', '$100,000']
                },
                category='insurance_bonding',
                difficulty='medium',
                expected_keywords=['surety', 'bond', 'cost', 'premium']
            ),
            QuestionTemplate(
                "Is workers compensation insurance required for contractors in {state}?",
                {
                    'state': self.states
                },
                category='insurance_bonding',
                difficulty='medium',
                expected_keywords=['workers compensation', 'required', 'contractors']
            )
        ]
        
        # 6. Financial Planning & ROI
        templates['financial_planning_roi'] = [
            QuestionTemplate(
                "What's the average ROI on getting a contractor license?",
                {},
                category='financial_planning_roi',
                difficulty='medium',
                expected_keywords=['ROI', 'contractor', 'license', 'return']
            ),
            QuestionTemplate(
                "How much can I increase my income with a contractor license?",
                {},
                category='financial_planning_roi',
                difficulty='medium',
                expected_keywords=['income', 'increase', 'contractor', 'license']
            ),
            QuestionTemplate(
                "What are the total costs to get a contractor license in {state}?",
                {
                    'state': self.states
                },
                category='financial_planning_roi',
                difficulty='medium',
                expected_keywords=['costs', 'total', 'contractor', 'license']
            ),
            QuestionTemplate(
                "How quickly can I recover the investment in my contractor license?",
                {},
                category='financial_planning_roi',
                difficulty='hard',
                expected_keywords=['recover', 'investment', 'contractor', 'license']
            ),
            QuestionTemplate(
                "Should I finance my contractor license training and fees?",
                {},
                category='financial_planning_roi',
                difficulty='hard',
                expected_keywords=['finance', 'training', 'fees', 'license']
            )
        ]
        
        # 7. Success Stories & Case Studies
        templates['success_stories_case_studies'] = [
            QuestionTemplate(
                "Can you share a success story of someone who got their contractor license?",
                {},
                category='success_stories_case_studies',
                difficulty='easy',
                expected_keywords=['success', 'story', 'contractor', 'license']
            ),
            QuestionTemplate(
                "What results have other contractors seen after getting licensed?",
                {},
                category='success_stories_case_studies',
                difficulty='medium',
                expected_keywords=['results', 'contractors', 'licensed', 'benefits']
            ),
            QuestionTemplate(
                "How has getting licensed changed contractors' businesses?",
                {},
                category='success_stories_case_studies',
                difficulty='medium',
                expected_keywords=['licensed', 'changed', 'business', 'contractors']
            ),
            QuestionTemplate(
                "What's the typical income increase after getting a contractor license?",
                {},
                category='success_stories_case_studies',
                difficulty='hard',
                expected_keywords=['income', 'increase', 'contractor', 'license']
            ),
            QuestionTemplate(
                "Can you show me before and after examples of licensed contractors?",
                {},
                category='success_stories_case_studies',
                difficulty='medium',
                expected_keywords=['before', 'after', 'examples', 'licensed']
            )
        ]
        
        # 8. Troubleshooting & Problem Resolution
        templates['troubleshooting_problem_resolution'] = [
            QuestionTemplate(
                "What should I do if my contractor license application is denied?",
                {},
                category='troubleshooting_problem_resolution',
                difficulty='hard',
                expected_keywords=['application', 'denied', 'license', 'appeal']
            ),
            QuestionTemplate(
                "I failed the contractor exam, what are my options?",
                {},
                category='troubleshooting_problem_resolution',
                difficulty='medium',
                expected_keywords=['failed', 'exam', 'retake', 'options']
            ),
            QuestionTemplate(
                "How do I handle a complaint against my contractor license?",
                {},
                category='troubleshooting_problem_resolution',
                difficulty='hard',
                expected_keywords=['complaint', 'license', 'disciplinary', 'response']
            ),
            QuestionTemplate(
                "What happens if I let my contractor license expire?",
                {},
                category='troubleshooting_problem_resolution',
                difficulty='medium',
                expected_keywords=['expire', 'license', 'renewal', 'reinstate']
            ),
            QuestionTemplate(
                "I'm having trouble with the {state} licensing board, what should I do?",
                {
                    'state': self.states
                },
                category='troubleshooting_problem_resolution',
                difficulty='hard',
                expected_keywords=['licensing', 'board', 'trouble', 'help']
            )
        ]
        
        return templates
    
    def _create_scenario_questions(self) -> List[TestQuestion]:
        """Create scenario-based questions for realistic testing"""
        scenarios = [
            {
                'text': "I'm a construction worker with 5 years of experience in Georgia. I want to start my own general contracting business. What steps do I need to take to get licensed?",
                'category': 'state_licensing_requirements',
                'state': 'GA',
                'difficulty': 'hard',
                'question_type': 'scenario',
                'expected_keywords': ['license', 'steps', 'Georgia', 'general contractor']
            },
            {
                'text': "I just failed my contractor exam in California by 2 points. I'm feeling discouraged. What should I do next?",
                'category': 'troubleshooting_problem_resolution',
                'state': 'CA',
                'difficulty': 'medium',
                'question_type': 'scenario',
                'expected_keywords': ['failed', 'exam', 'retake', 'California']
            },
            {
                'text': "I have $5,000 to invest in getting my contractor license. Will this be enough, and what's my expected ROI?",
                'category': 'financial_planning_roi',
                'difficulty': 'hard',
                'question_type': 'scenario',
                'expected_keywords': ['invest', 'license', 'ROI', 'cost']
            },
            {
                'text': "I'm currently working as a subcontractor but want to bid on larger projects. Do I really need a license?",
                'category': 'business_formation_operations',
                'difficulty': 'medium',
                'question_type': 'scenario',
                'expected_keywords': ['subcontractor', 'bid', 'projects', 'license']
            },
            {
                'text': "I'm 55 years old and have been in construction for 30 years. Is it worth getting licensed now?",
                'category': 'success_stories_case_studies',
                'difficulty': 'hard',
                'question_type': 'scenario',
                'expected_keywords': ['worth', 'licensed', 'experience', 'career']
            }
        ]
        
        questions = []
        for i, scenario in enumerate(scenarios):
            question = TestQuestion(
                id=f"scenario_{i+1}_{random.randint(1000, 9999)}",
                text=scenario['text'],
                category=scenario['category'],
                state=scenario.get('state'),
                difficulty=scenario['difficulty'],
                question_type=scenario['question_type'],
                expected_keywords=scenario['expected_keywords']
            )
            questions.append(question)
        
        return questions
    
    def _create_comparison_questions(self) -> List[TestQuestion]:
        """Create comparison questions between states or options"""
        comparisons = [
            {
                'text': "What are the differences between contractor licensing requirements in California vs Texas?",
                'category': 'state_licensing_requirements',
                'difficulty': 'hard',
                'question_type': 'comparison',
                'expected_keywords': ['differences', 'California', 'Texas', 'requirements']
            },
            {
                'text': "Should I get a specialty license or a general contractor license?",
                'category': 'state_licensing_requirements',
                'difficulty': 'medium',
                'question_type': 'comparison',
                'expected_keywords': ['specialty', 'general', 'license', 'difference']
            },
            {
                'text': "Is it better to join a qualifier network or get my own license?",
                'category': 'qualifier_network_programs',
                'difficulty': 'hard',
                'question_type': 'comparison',
                'expected_keywords': ['qualifier', 'network', 'own license', 'better']
            },
            {
                'text': "What's more cost-effective: getting licensed or staying unlicensed?",
                'category': 'financial_planning_roi',
                'difficulty': 'hard',
                'question_type': 'comparison',
                'expected_keywords': ['cost-effective', 'licensed', 'unlicensed', 'compare']
            }
        ]
        
        questions = []
        for i, comparison in enumerate(comparisons):
            question = TestQuestion(
                id=f"comparison_{i+1}_{random.randint(1000, 9999)}",
                text=comparison['text'],
                category=comparison['category'],
                difficulty=comparison['difficulty'],
                question_type=comparison['question_type'],
                expected_keywords=comparison['expected_keywords']
            )
            questions.append(question)
        
        return questions
    
    def _create_edge_case_questions(self) -> List[TestQuestion]:
        """Create edge case questions to test system robustness"""
        edge_cases = [
            {
                'text': "Can I get a contractor license if I have a felony conviction?",
                'category': 'troubleshooting_problem_resolution',
                'difficulty': 'hard',
                'expected_keywords': ['license', 'felony', 'conviction', 'eligible']
            },
            {
                'text': "What's the minimum age to get a contractor license?",
                'category': 'state_licensing_requirements',
                'difficulty': 'medium',
                'expected_keywords': ['minimum', 'age', 'license', 'requirements']
            },
            {
                'text': "Do I need to renew my contractor license, and how often?",
                'category': 'state_licensing_requirements',
                'difficulty': 'easy',
                'expected_keywords': ['renew', 'license', 'how often', 'renewal']
            },
            {
                'text': "Can I transfer my contractor license from one state to another?",
                'category': 'state_licensing_requirements',
                'difficulty': 'hard',
                'expected_keywords': ['transfer', 'license', 'state', 'reciprocity']
            },
            {
                'text': "What happens to my license if I file for bankruptcy?",
                'category': 'troubleshooting_problem_resolution',
                'difficulty': 'hard',
                'expected_keywords': ['license', 'bankruptcy', 'suspend', 'revoke']
            }
        ]
        
        questions = []
        for i, edge_case in enumerate(edge_cases):
            question = TestQuestion(
                id=f"edge_case_{i+1}_{random.randint(1000, 9999)}",
                text=edge_case['text'],
                category=edge_case['category'],
                difficulty=edge_case['difficulty'],
                question_type='edge_case',
                expected_keywords=edge_case['expected_keywords']
            )
            questions.append(question)
        
        return questions
    
    async def generate_questions(self, count: int = 200, 
                               categories: List[str] = None,
                               difficulty_distribution: Dict[str, float] = None) -> List[TestQuestion]:
        """
        Generate comprehensive set of test questions.
        
        Args:
            count: Total number of questions to generate
            categories: List of categories to include (None = all)
            difficulty_distribution: Distribution of difficulties {'easy': 0.4, 'medium': 0.4, 'hard': 0.2}
            
        Returns:
            List of TestQuestion objects
        """
        logger.info(f"Generating {count} synthetic test questions")
        
        if categories is None:
            categories = list(self.question_templates.keys())
        
        if difficulty_distribution is None:
            difficulty_distribution = {'easy': 0.3, 'medium': 0.5, 'hard': 0.2}
        
        # Calculate questions per category
        questions_per_category = max(1, count // len(categories))
        
        all_questions = []
        
        # Generate questions from templates
        for category in categories:
            if category not in self.question_templates:
                logger.warning(f"Unknown category: {category}")
                continue
            
            templates = self.question_templates[category]
            category_questions = []
            
            # Generate questions from each template in the category
            questions_per_template = max(1, questions_per_category // len(templates))
            
            for template in templates:
                template_questions = template.generate_questions(questions_per_template)
                category_questions.extend(template_questions)
            
            # Trim to exact count needed
            if len(category_questions) > questions_per_category:
                category_questions = random.sample(category_questions, questions_per_category)
            
            all_questions.extend(category_questions)
        
        # Add scenario questions (10% of total)
        scenario_count = max(1, count // 10)
        scenario_questions = self._create_scenario_questions()
        if len(scenario_questions) > scenario_count:
            scenario_questions = random.sample(scenario_questions, scenario_count)
        all_questions.extend(scenario_questions)
        
        # Add comparison questions (5% of total)
        comparison_count = max(1, count // 20)
        comparison_questions = self._create_comparison_questions()
        if len(comparison_questions) > comparison_count:
            comparison_questions = random.sample(comparison_questions, comparison_count)
        all_questions.extend(comparison_questions)
        
        # Add edge case questions (5% of total)
        edge_case_count = max(1, count // 20)
        edge_case_questions = self._create_edge_case_questions()
        if len(edge_case_questions) > edge_case_count:
            edge_case_questions = random.sample(edge_case_questions, edge_case_count)
        all_questions.extend(edge_case_questions)
        
        # Trim to exact count and shuffle
        if len(all_questions) > count:
            all_questions = random.sample(all_questions, count)
        
        random.shuffle(all_questions)
        
        logger.info(f"Generated {len(all_questions)} questions across {len(categories)} categories")
        
        # Log category distribution
        category_counts = {}
        for question in all_questions:
            category_counts[question.category] = category_counts.get(question.category, 0) + 1
        
        logger.info(f"Category distribution: {category_counts}")
        
        return all_questions
    
    def generate_category_specific_questions(self, category: str, count: int = 50) -> List[TestQuestion]:
        """Generate questions for a specific category"""
        if category not in self.question_templates:
            raise ValueError(f"Unknown category: {category}")
        
        templates = self.question_templates[category]
        questions = []
        
        questions_per_template = max(1, count // len(templates))
        
        for template in templates:
            template_questions = template.generate_questions(questions_per_template)
            questions.extend(template_questions)
        
        # Trim to exact count
        if len(questions) > count:
            questions = random.sample(questions, count)
        
        return questions
    
    def export_questions(self, questions: List[TestQuestion], 
                        filename: str = None) -> str:
        """Export questions to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"synthetic_questions_{timestamp}.json"
        
        export_data = {
            'generated_at': datetime.now().isoformat(),
            'total_questions': len(questions),
            'categories': list(set(q.category for q in questions)),
            'difficulty_distribution': {
                difficulty: sum(1 for q in questions if q.difficulty == difficulty)
                for difficulty in ['easy', 'medium', 'hard']
            },
            'questions': [q.to_dict() for q in questions]
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(questions)} questions to {filename}")
        return filename
    
    def load_questions_from_file(self, filename: str) -> List[TestQuestion]:
        """Load questions from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        questions = []
        for q_data in data['questions']:
            question = TestQuestion(**q_data)
            questions.append(question)
        
        logger.info(f"Loaded {len(questions)} questions from {filename}")
        return questions


# Testing and utility functions
async def generate_sample_questions():
    """Generate sample questions for testing"""
    generator = SyntheticQuestionGenerator()
    
    # Generate questions for each category
    categories = [
        'state_licensing_requirements',
        'exam_preparation_testing',
        'qualifier_network_programs',
        'business_formation_operations',
        'insurance_bonding',
        'financial_planning_roi',
        'success_stories_case_studies',
        'troubleshooting_problem_resolution'
    ]
    
    all_questions = await generator.generate_questions(
        count=200,
        categories=categories
    )
    
    # Export to file
    filename = generator.export_questions(all_questions)
    
    # Show sample questions
    print(f"Generated {len(all_questions)} sample questions")
    print(f"Exported to: {filename}")
    
    for category in categories:
        category_questions = [q for q in all_questions if q.category == category]
        if category_questions:
            print(f"\n{category.upper()} ({len(category_questions)} questions):")
            for q in category_questions[:2]:  # Show first 2 questions
                print(f"  - {q.text}")
    
    return all_questions


if __name__ == "__main__":
    # Generate sample questions
    import asyncio
    asyncio.run(generate_sample_questions())