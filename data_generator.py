import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string
from typing import List, Dict, Any
from faker import Faker

class DataGenerator:
    """Generate synthetic data based on schema or existing data analysis."""
    
    def __init__(self):
        self.fake = Faker()
        self.fake.seed_instance(42)  # For reproducible results
        np.random.seed(42)
        random.seed(42)
    
    def generate_from_schema(self, columns: List[Dict[str, Any]], num_samples: int) -> pd.DataFrame:
        """
        Generate synthetic data from schema column definitions.
        
        Args:
            columns: List of column definitions from schema parser
            num_samples: Number of rows to generate
            
        Returns:
            DataFrame with synthetic data
        """
        data = {}
        unique_counters = {}  # Track counters for unique/auto-increment fields
        
        for column in columns:
            col_name = column['name']
            col_type = column['type']
            params = column.get('params', {})
            
            # Generate data based on column type
            if col_type == 'integer':
                data[col_name] = self._generate_integers(num_samples, params, unique_counters, col_name)
            elif col_type == 'float':
                data[col_name] = self._generate_floats(num_samples, params)
            elif col_type == 'string':
                data[col_name] = self._generate_strings(num_samples, params, col_name)
            elif col_type == 'date':
                data[col_name] = self._generate_dates(num_samples, params)
            elif col_type == 'datetime':
                data[col_name] = self._generate_datetimes(num_samples, params)
            elif col_type == 'boolean':
                data[col_name] = self._generate_booleans(num_samples, params)
            else:
                # Default to string for unknown types
                data[col_name] = self._generate_strings(num_samples, params, col_name)
        
        return pd.DataFrame(data)
    
    def generate_from_analysis(self, analysis: Dict[str, Any], num_samples: int) -> pd.DataFrame:
        """
        Generate synthetic data based on existing data analysis.
        
        Args:
            analysis: Analysis results from DataAnalyzer
            num_samples: Number of rows to generate
            
        Returns:
            DataFrame with synthetic data
        """
        data = {}
        
        for col_name, col_info in analysis['column_info'].items():
            col_type = col_info['type']
            
            if col_type == 'numeric':
                data[col_name] = self._generate_from_numeric_analysis(num_samples, col_info)
            elif col_type == 'categorical':
                data[col_name] = self._generate_from_categorical_analysis(num_samples, col_info)
            elif col_type == 'datetime':
                data[col_name] = self._generate_from_datetime_analysis(num_samples, col_info)
            elif col_type == 'boolean':
                data[col_name] = self._generate_from_boolean_analysis(num_samples, col_info)
            else:
                # Default to categorical
                data[col_name] = self._generate_from_categorical_analysis(num_samples, col_info)
        
        return pd.DataFrame(data)
    
    def _generate_integers(self, num_samples: int, params: Dict[str, Any], 
                          unique_counters: Dict[str, int], col_name: str) -> List[int]:
        """Generate integer values."""
        min_val = params.get('min_value', 1)
        max_val = params.get('max_value', 100000)
        nullable = params.get('nullable', False)
        unique = params.get('unique', False)
        auto_increment = params.get('auto_increment', False)
        
        if auto_increment:
            # Generate sequential IDs
            start_val = unique_counters.get(col_name, 1)
            values = list(range(start_val, start_val + num_samples))
            unique_counters[col_name] = start_val + num_samples
        elif unique:
            # Generate unique random integers
            if max_val - min_val + 1 < num_samples:
                # Expand range if needed
                max_val = min_val + num_samples
            values = random.sample(range(min_val, max_val + 1), num_samples)
        else:
            # Generate random integers
            values = [random.randint(min_val, max_val) for _ in range(num_samples)]
        
        # Add null values if nullable
        if nullable:
            null_count = int(num_samples * 0.05)  # 5% null values
            null_indices = random.sample(range(num_samples), null_count)
            for idx in null_indices:
                values[idx] = None
        
        return values
    
    def _generate_floats(self, num_samples: int, params: Dict[str, Any]) -> List[float]:
        """Generate float values."""
        min_val = params.get('min_value', 0.0)
        max_val = params.get('max_value', 10000.0)
        precision = params.get('precision', None)
        scale = params.get('scale', 2)
        nullable = params.get('nullable', False)
        
        values = []
        for _ in range(num_samples):
            value = random.uniform(min_val, max_val)
            if precision:
                # Round to specified decimal places
                value = round(value, scale)
            values.append(value)
        
        # Add null values if nullable
        if nullable:
            null_count = int(num_samples * 0.05)
            null_indices = random.sample(range(num_samples), null_count)
            for idx in null_indices:
                values[idx] = None
        
        return values
    
    def _generate_strings(self, num_samples: int, params: Dict[str, Any], col_name: str) -> List[str]:
        """Generate string values."""
        min_length = params.get('min_length', 1)
        max_length = params.get('max_length', 255)
        nullable = params.get('nullable', False)
        unique = params.get('unique', False)
        
        # Choose appropriate faker method based on column name
        faker_method = self._choose_faker_method(col_name)
        
        values = []
        used_values = set()
        
        for _ in range(num_samples):
            if faker_method:
                # Use Faker for realistic data
                value = str(getattr(self.fake, faker_method)())
            else:
                # Generate random string
                length = random.randint(min_length, min(max_length, 50))
                value = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))
            
            # Ensure uniqueness if required
            if unique:
                counter = 1
                original_value = value
                while value in used_values:
                    value = f"{original_value}_{counter}"
                    counter += 1
                used_values.add(value)
            
            # Truncate if too long
            if len(value) > max_length:
                value = value[:max_length]
            
            values.append(value)
        
        # Add null values if nullable
        if nullable:
            null_count = int(num_samples * 0.05)
            null_indices = random.sample(range(num_samples), null_count)
            for idx in null_indices:
                values[idx] = None
        
        return values
    
    def _choose_faker_method(self, col_name: str) -> str:
        """Choose appropriate Faker method based on column name."""
        col_lower = col_name.lower()
        
        if any(keyword in col_lower for keyword in ['name', 'first_name', 'lastname']):
            return 'name'
        elif any(keyword in col_lower for keyword in ['email', 'mail']):
            return 'email'
        elif any(keyword in col_lower for keyword in ['phone', 'mobile', 'tel']):
            return 'phone_number'
        elif any(keyword in col_lower for keyword in ['address', 'street']):
            return 'address'
        elif any(keyword in col_lower for keyword in ['city']):
            return 'city'
        elif any(keyword in col_lower for keyword in ['state', 'province']):
            return 'state'
        elif any(keyword in col_lower for keyword in ['country']):
            return 'country'
        elif any(keyword in col_lower for keyword in ['company', 'organization']):
            return 'company'
        elif any(keyword in col_lower for keyword in ['job', 'position', 'title']):
            return 'job'
        elif any(keyword in col_lower for keyword in ['description', 'text', 'comment']):
            return 'text'
        else:
            return None
    
    def _generate_dates(self, num_samples: int, params: Dict[str, Any]) -> List:
        """Generate date values."""
        start_date = datetime.strptime(params.get('start_date', '2020-01-01'), '%Y-%m-%d').date()
        end_date = datetime.strptime(params.get('end_date', '2024-12-31'), '%Y-%m-%d').date()
        nullable = params.get('nullable', False)
        
        values = []
        for _ in range(num_samples):
            random_date = self.fake.date_between(start_date=start_date, end_date=end_date)
            values.append(random_date)
        
        # Add null values if nullable
        if nullable:
            null_count = int(num_samples * 0.05)
            null_indices = random.sample(range(num_samples), null_count)
            for idx in null_indices:
                values[idx] = None
        
        return values
    
    def _generate_datetimes(self, num_samples: int, params: Dict[str, Any]) -> List:
        """Generate datetime values."""
        start_date = datetime.strptime(params.get('start_date', '2020-01-01'), '%Y-%m-%d')
        end_date = datetime.strptime(params.get('end_date', '2024-12-31'), '%Y-%m-%d')
        nullable = params.get('nullable', False)
        
        values = []
        for _ in range(num_samples):
            random_datetime = self.fake.date_time_between(start_date=start_date, end_date=end_date)
            values.append(random_datetime)
        
        # Add null values if nullable
        if nullable:
            null_count = int(num_samples * 0.05)
            null_indices = random.sample(range(num_samples), null_count)
            for idx in null_indices:
                values[idx] = None
        
        return values
    
    def _generate_booleans(self, num_samples: int, params: Dict[str, Any]) -> List:
        """Generate boolean values."""
        true_prob = params.get('true_probability', 0.5)
        nullable = params.get('nullable', False)
        
        values = []
        for _ in range(num_samples):
            value = random.random() < true_prob
            values.append(value)
        
        # Add null values if nullable
        if nullable:
            null_count = int(num_samples * 0.05)
            null_indices = random.sample(range(num_samples), null_count)
            for idx in null_indices:
                values[idx] = None
        
        return values
    
    def _generate_from_numeric_analysis(self, num_samples: int, col_info: Dict[str, Any]) -> List:
        """Generate numeric data based on analysis of existing data."""
        stats = col_info.get('stats', {})
        min_val = stats.get('min', 0)
        max_val = stats.get('max', 100)
        mean = stats.get('mean', (min_val + max_val) / 2)
        std = stats.get('std', (max_val - min_val) / 4)
        
        # Generate using normal distribution with clipping
        values = np.random.normal(mean, std, num_samples)
        values = np.clip(values, min_val, max_val)
        
        # Add noise based on noise level
        noise_level = col_info.get('noise_level', 0.05)
        if noise_level > 0:
            noise = np.random.normal(0, std * noise_level, num_samples)
            values += noise
            values = np.clip(values, min_val, max_val)
        
        # Convert to integers if original data was integer
        if col_info.get('is_integer', False):
            values = values.astype(int)
        
        return values.tolist()
    
    def _generate_from_categorical_analysis(self, num_samples: int, col_info: Dict[str, Any]) -> List:
        """Generate categorical data based on analysis of existing data."""
        value_counts = col_info.get('value_counts', {})
        
        if not value_counts:
            # Fallback to random strings
            return [f"Category_{i}" for i in range(num_samples)]
        
        # Create weighted choices based on original distribution
        values = list(value_counts.keys())
        weights = list(value_counts.values())
        
        # Normalize weights
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        
        # Generate samples
        generated = np.random.choice(values, size=num_samples, p=probabilities)
        
        return generated.tolist()
    
    def _generate_from_datetime_analysis(self, num_samples: int, col_info: Dict[str, Any]) -> List:
        """Generate datetime data based on analysis of existing data."""
        stats = col_info.get('stats', {})
        min_date = stats.get('min')
        max_date = stats.get('max')
        
        if not min_date or not max_date:
            # Fallback to default date range
            min_date = datetime(2020, 1, 1)
            max_date = datetime(2024, 12, 31)
        
        # Generate random datetimes in the range
        values = []
        for _ in range(num_samples):
            random_datetime = self.fake.date_time_between(start_date=min_date, end_date=max_date)
            values.append(random_datetime)
        
        return values
    
    def _generate_from_boolean_analysis(self, num_samples: int, col_info: Dict[str, Any]) -> List:
        """Generate boolean data based on analysis of existing data."""
        stats = col_info.get('stats', {})
        true_ratio = stats.get('true_ratio', 0.5)
        
        values = []
        for _ in range(num_samples):
            value = random.random() < true_ratio
            values.append(value)
        
        return values