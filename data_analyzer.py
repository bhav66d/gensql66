import pandas as pd
import numpy as np
from datetime import datetime
import io
from typing import Dict, Any, Union

class DataAnalyzer:
    """Analyze existing data to understand patterns and distributions."""
    
    def __init__(self):
        self.supported_extensions = ['.csv', '.xlsx', '.xls']
    
    def analyze_file(self, uploaded_file, noise_level: float = 0.05) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        Analyze an uploaded file and return analysis results.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            noise_level: Amount of noise to add to synthetic data (0-1)
            
        Returns:
            Analysis dictionary or dict of sheet analyses for Excel files
        """
        file_extension = self._get_file_extension(uploaded_file.name)
        
        if file_extension == '.csv':
            return self._analyze_csv(uploaded_file, noise_level)
        elif file_extension in ['.xlsx', '.xls']:
            return self._analyze_excel(uploaded_file, noise_level)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        return '.' + filename.split('.')[-1].lower()
    
    def _analyze_csv(self, uploaded_file, noise_level: float) -> Dict[str, Any]:
        """Analyze a CSV file."""
        # Read CSV
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding='latin-1')
        
        return self._analyze_dataframe(df, noise_level)
    
    def _analyze_excel(self, uploaded_file, noise_level: float) -> Dict[str, Dict[str, Any]]:
        """Analyze an Excel file (potentially multiple sheets)."""
        # Read all sheets
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_analyses = {}
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
            sheet_analyses[sheet_name] = self._analyze_dataframe(df, noise_level)
        
        return sheet_analyses
    
    def _analyze_dataframe(self, df: pd.DataFrame, noise_level: float) -> Dict[str, Any]:
        """
        Analyze a pandas DataFrame and extract patterns.
        
        Args:
            df: DataFrame to analyze
            noise_level: Noise level for synthetic data generation
            
        Returns:
            Dictionary containing analysis results
        """
        analysis = {
            'rows': len(df),
            'columns': len(df.columns),
            'column_info': {},
            'noise_level': noise_level
        }
        
        for column in df.columns:
            col_analysis = self._analyze_column(df[column])
            analysis['column_info'][column] = col_analysis
        
        return analysis
    
    def _analyze_column(self, series: pd.Series) -> Dict[str, Any]:
        """
        Analyze a single column/series.
        
        Args:
            series: Pandas Series to analyze
            
        Returns:
            Dictionary with column analysis
        """
        col_info = {
            'name': series.name,
            'dtype': str(series.dtype),
            'missing_count': series.isnull().sum(),
            'missing_percent': (series.isnull().sum() / len(series)) * 100,
            'unique_count': series.nunique(),
            'unique_percent': (series.nunique() / len(series)) * 100
        }
        
        # Remove null values for analysis
        non_null_series = series.dropna()
        
        if len(non_null_series) == 0:
            col_info['type'] = 'empty'
            return col_info
        
        # Determine column type and analyze accordingly
        if self._is_numeric_column(non_null_series):
            col_info.update(self._analyze_numeric_column(non_null_series))
        elif self._is_datetime_column(non_null_series):
            col_info.update(self._analyze_datetime_column(non_null_series))
        elif self._is_boolean_column(non_null_series):
            col_info.update(self._analyze_boolean_column(non_null_series))
        else:
            col_info.update(self._analyze_categorical_column(non_null_series))
        
        return col_info
    
    def _is_numeric_column(self, series: pd.Series) -> bool:
        """Check if column contains numeric data."""
        return pd.api.types.is_numeric_dtype(series) or self._can_convert_to_numeric(series)
    
    def _can_convert_to_numeric(self, series: pd.Series) -> bool:
        """Check if string column can be converted to numeric."""
        try:
            pd.to_numeric(series.head(min(100, len(series))))
            return True
        except (ValueError, TypeError):
            return False
    
    def _is_datetime_column(self, series: pd.Series) -> bool:
        """Check if column contains datetime data."""
        if pd.api.types.is_datetime64_any_dtype(series):
            return True
        
        # Try to parse as datetime
        if series.dtype == 'object':
            try:
                pd.to_datetime(series.head(min(10, len(series))))
                return True
            except (ValueError, TypeError):
                return False
        
        return False
    
    def _is_boolean_column(self, series: pd.Series) -> bool:
        """Check if column contains boolean data."""
        if pd.api.types.is_bool_dtype(series):
            return True
        
        # Check if all values are boolean-like
        unique_values = set(series.astype(str).str.lower().unique())
        boolean_values = {'true', 'false', '1', '0', 'yes', 'no', 'y', 'n'}
        
        return len(unique_values) <= 2 and unique_values.issubset(boolean_values)
    
    def _analyze_numeric_column(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze numeric column."""
        # Convert to numeric if needed
        if not pd.api.types.is_numeric_dtype(series):
            numeric_series = pd.to_numeric(series, errors='coerce')
        else:
            numeric_series = series
        
        # Check if it's integer-like
        #is_integer = all(x.is_integer() for x in numeric_series if pd.notna(x) and isinstance(x, (int, float)))
        is_integer = all(x.is_integer() if isinstance(x, float) else isinstance(x, int) for x in numeric_series if pd.notna(x))
        
        stats = {
            'min': float(numeric_series.min()),
            'max': float(numeric_series.max()),
            'mean': float(numeric_series.mean()),
            'median': float(numeric_series.median()),
            'std': float(numeric_series.std()),
            'q25': float(numeric_series.quantile(0.25)),
            'q75': float(numeric_series.quantile(0.75))
        }
        
        return {
            'type': 'numeric',
            'is_integer': is_integer,
            'stats': stats,
            'distribution': self._get_distribution_info(numeric_series)
        }
    
    def _analyze_datetime_column(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze datetime column."""
        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(series):
            datetime_series = pd.to_datetime(series, errors='coerce')
        else:
            datetime_series = series
        
        stats = {
            'min': datetime_series.min(),
            'max': datetime_series.max(),
            'range_days': (datetime_series.max() - datetime_series.min()).days
        }
        
        return {
            'type': 'datetime',
            'stats': stats,
            'format_examples': datetime_series.head(3).astype(str).tolist()
        }
    
    def _analyze_boolean_column(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze boolean column."""
        # Convert to boolean
        bool_mapping = {
            'true': True, 'false': False,
            '1': True, '0': False,
            'yes': True, 'no': False,
            'y': True, 'n': False
        }
        
        bool_series = series.astype(str).str.lower().map(bool_mapping)
        
        true_count = bool_series.sum()
        total_count = len(bool_series)
        
        stats = {
            'true_count': int(true_count),
            'false_count': int(total_count - true_count),
            'true_ratio': float(true_count / total_count) if total_count > 0 else 0.5
        }
        
        return {
            'type': 'boolean',
            'stats': stats
        }
    
    def _analyze_categorical_column(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze categorical column."""
        value_counts = series.value_counts()
        
        # Get top categories (limit to prevent memory issues)
        top_categories = value_counts.head(50).to_dict()
        
        stats = {
            'most_common': value_counts.index[0] if len(value_counts) > 0 else None,
            'most_common_count': int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
            'category_count': len(value_counts)
        }
        
        return {
            'type': 'categorical',
            'value_counts': top_categories,
            'stats': stats,
            'examples': series.head(5).tolist()
        }
    
    def _get_distribution_info(self, series: pd.Series) -> Dict[str, Any]:
        """Get distribution information for numeric data."""
        try:
            # Basic distribution analysis
            skewness = float(series.skew())
            kurtosis = float(series.kurtosis())
            
            # Detect potential distribution type
            distribution_type = 'normal'  # Default
            
            if abs(skewness) > 1:
                distribution_type = 'skewed'
            elif series.min() >= 0 and (series.max() - series.min()) / series.std() < 2:
                distribution_type = 'uniform'
            
            return {
                'skewness': skewness,
                'kurtosis': kurtosis,
                'type': distribution_type
            }
        except Exception:
            return {'type': 'unknown'}
    
    def get_column_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the analysis."""
        summary_parts = []
        
        summary_parts.append(f"Dataset contains {analysis['rows']} rows and {analysis['columns']} columns.")
        
        type_counts = {}
        for col_info in analysis['column_info'].values():
            col_type = col_info['type']
            type_counts[col_type] = type_counts.get(col_type, 0) + 1
        
        type_summary = ', '.join([f"{count} {type_name}" for type_name, count in type_counts.items()])
        summary_parts.append(f"Column types: {type_summary}.")
        
        # Identify potential issues
        high_missing_cols = [
            col_name for col_name, col_info in analysis['column_info'].items()
            if col_info['missing_percent'] > 20
        ]
        
        if high_missing_cols:
            summary_parts.append(f"Columns with high missing values (>20%): {', '.join(high_missing_cols)}")
        
        return ' '.join(summary_parts)