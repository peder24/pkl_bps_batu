import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class DataProcessor:
    def __init__(self, csv_file='data_iph_modeling.csv'):
        self.csv_file = csv_file
        self.feature_columns = ['Lag_1', 'Lag_2', 'Lag_3', 'Lag_4', 'MA_3', 'MA_7']
        self.data = self.load_data()
        
    def load_data(self):
        """Load data from CSV file"""
        try:
            if not os.path.exists(self.csv_file):
                raise FileNotFoundError(f"File {self.csv_file} tidak ditemukan!")
            
            print(f"📊 Loading data from {self.csv_file}")
            df = pd.read_csv(self.csv_file)
            
            # Convert date column to datetime
            if 'Tanggal' in df.columns:
                df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
            else:
                raise ValueError("Kolom 'Tanggal' tidak ditemukan dalam CSV")
            
            # Check required columns
            required_columns = ['Indikator_Harga'] + self.feature_columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Kolom yang hilang: {missing_columns}")
            
            # Clean data
            df = self.clean_data(df)
            
            print(f"✅ Data loaded successfully: {len(df)} records")
            print(f"📅 Date range: {df['Tanggal'].min()} to {df['Tanggal'].max()}")
            
            return df
                
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            raise
    
    def clean_data(self, df):
        """Clean and validate data"""
        original_length = len(df)
        
        # Remove rows with missing target variable
        df = df.dropna(subset=['Indikator_Harga'])
        
        # Handle missing values in feature columns
        for col in self.feature_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0.0)
        
        # Sort by date
        df = df.sort_values('Tanggal').reset_index(drop=True)
        
        if len(df) < original_length:
            print(f"🧹 Cleaned data: removed {original_length - len(df)} rows")
        
        return df
    
    def get_historical_data(self, months=None):
        """Get historical data - DIPERBAIKI untuk konsistensi dengan notebook"""
        df = self.data.copy()
        
        # PERBAIKAN: Untuk visualisasi saja, bukan untuk model training/prediction
        if months and months > 0:
            # Hanya untuk display di chart, bukan untuk model
            cutoff_date = df['Tanggal'].max() - pd.DateOffset(months=months)
            df_display = df[df['Tanggal'] >= cutoff_date]
            print(f"📊 Display data filtered to {months} months: {len(df_display)} records")
            print(f"📅 Display date range: {df_display['Tanggal'].min()} to {df_display['Tanggal'].max()}")
            return df_display
        
        # Return semua data untuk model (seperti notebook)
        print(f"📊 Using ALL data for model: {len(df)} records")
        return df
    
    def get_all_data(self):
        """Get ALL data tanpa filter - untuk konsistensi dengan notebook"""
        return self.data.copy()
    
    def get_latest_features(self):
        """Get latest features for prediction - DIPERBAIKI"""
        # PERBAIKAN: Gunakan SEMUA data seperti di notebook
        all_data = self.get_all_data()
        
        if len(all_data) == 0:
            raise ValueError("No data available for feature extraction")
        
        # Ambil features dari row terakhir (sudah dihitung dengan semua data)
        latest_row = all_data.iloc[-1]
        features = []
        
        for col in self.feature_columns:
            if col in latest_row:
                features.append(latest_row[col])
            else:
                features.append(0.0)
        
        print(f"🎯 Latest features (from ALL data): {features}")
        return np.array([features])
    
    def prepare_features(self, df):
        """Prepare features for model prediction"""
        features = []
        for col in self.feature_columns:
            if col in df.columns:
                features.append(df[col].values)
            else:
                features.append(np.zeros(len(df)))
        
        return np.array(features).T
    
    def get_train_test_split(self, test_size=0.2):
        """Get train/test split for model evaluation"""
        # PERBAIKAN: Gunakan semua data
        all_data = self.get_all_data()
        
        if len(all_data) == 0:
            raise ValueError("No data available for train/test split")
        
        df_sorted = all_data.sort_values('Tanggal')
        
        split_idx = int(len(df_sorted) * (1 - test_size))
        
        train_data = df_sorted.iloc[:split_idx]
        test_data = df_sorted.iloc[split_idx:]
        
        X_train = self.prepare_features(train_data)
        y_train = train_data['Indikator_Harga'].values
        
        X_test = self.prepare_features(test_data)
        y_test = test_data['Indikator_Harga'].values
        
        return X_train, X_test, y_train, y_test
    
    def generate_forecast_features(self, n_steps=4):
        """Generate features for multi-step forecasting - DIPERBAIKI seperti notebook"""
        try:
            # PERBAIKAN: Gunakan SEMUA data seperti di notebook
            all_data = self.get_all_data()
            
            if len(all_data) < 7:
                raise ValueError(f"Insufficient data: {len(all_data)} records")
            
            # Ambil features terakhir dari semua data (seperti notebook)
            last_features = all_data[self.feature_columns].iloc[-1].values
            print(f"🔍 Starting forecast from features: {last_features}")
            
            forecast_features = []
            current_features = last_features.copy()
            
            for step in range(n_steps):
                # Gunakan features saat ini untuk prediksi
                forecast_features.append(current_features.copy())
                
                print(f"   Step {step+1}: {current_features}")
                
                # Update features untuk langkah berikutnya (seperti di notebook)
                # Simulasi update berdasarkan pola forecasting
                new_features = np.zeros_like(current_features)
                
                # Shift lag features (simulasi seperti notebook)
                new_features[0] = current_features[0]  # Lag_1 (akan diupdate dengan prediksi)
                new_features[1] = current_features[0]  # Lag_2 = previous Lag_1
                new_features[2] = current_features[1]  # Lag_3 = previous Lag_2
                new_features[3] = current_features[2]  # Lag_4 = previous Lag_3
                
                # Update moving averages (simulasi)
                new_features[4] = np.mean([new_features[0], new_features[1], new_features[2]])  # MA_3
                new_features[5] = np.mean([new_features[0], new_features[1], new_features[2], new_features[3]])  # MA_7 simplified
                
                current_features = new_features
            
            return np.array(forecast_features)
            
        except Exception as e:
            print(f"❌ Error in generate_forecast_features: {str(e)}")
            raise
    
    def get_data_summary(self):
        """Get summary statistics of the data"""
        all_data = self.get_all_data()
        
        if len(all_data) == 0:
            return {}
        
        summary = {
            'total_records': len(all_data),
            'date_range': {
                'start': all_data['Tanggal'].min().strftime('%Y-%m-%d'),
                'end': all_data['Tanggal'].max().strftime('%Y-%m-%d')
            },
            'iph_stats': {
                'mean': float(all_data['Indikator_Harga'].mean()),
                'std': float(all_data['Indikator_Harga'].std()),
                'min': float(all_data['Indikator_Harga'].min()),
                'max': float(all_data['Indikator_Harga'].max())
            },
            'latest_iph': float(all_data['Indikator_Harga'].iloc[-1]),
            'latest_features': all_data[self.feature_columns].iloc[-1].tolist()
        }
        return summary
    
    def add_new_data(self, date, iph_value):
        """Add new actual data point"""
        try:
            new_date = pd.to_datetime(date)
            
            # Calculate features based on recent data
            all_data = self.get_all_data()
            recent_values = all_data['Indikator_Harga'].tail(7).tolist()
            
            # Calculate lag features
            lag_1 = recent_values[-1] if len(recent_values) >= 1 else 0
            lag_2 = recent_values[-2] if len(recent_values) >= 2 else 0
            lag_3 = recent_values[-3] if len(recent_values) >= 3 else 0
            lag_4 = recent_values[-4] if len(recent_values) >= 4 else 0
            
            # Add new value for MA calculation
            recent_values.append(iph_value)
            ma_3 = np.mean(recent_values[-3:])
            ma_7 = np.mean(recent_values[-7:])
            
            # Create new row
            new_row = {
                'Periode': len(all_data) + 1,
                'Tanggal': new_date,
                'Indikator_Harga': iph_value,
                'Lag_1': lag_1,
                'Lag_2': lag_2,
                'Lag_3': lag_3,
                'Lag_4': lag_4,
                'MA_3': ma_3,
                'MA_7': ma_7
            }
            
            # Add to dataframe
            self.data = pd.concat([self.data, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save to CSV
            self.data.to_csv(self.csv_file, index=False)
            
            print(f"✅ Added new data point: {date} = {iph_value}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding new data: {e}")
            return False
    
    def get_notebook_comparison_data(self):
        """Get data for comparison with notebook results"""
        all_data = self.get_all_data()
        
        return {
            'total_records': len(all_data),
            'last_10_values': all_data['Indikator_Harga'].tail(10).tolist(),
            'latest_features': all_data[self.feature_columns].iloc[-1].tolist(),
            'latest_date': all_data['Tanggal'].iloc[-1].strftime('%Y-%m-%d'),
            'latest_iph': float(all_data['Indikator_Harga'].iloc[-1])
        }