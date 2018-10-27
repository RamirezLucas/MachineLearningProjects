import numpy as np
import proj1_helpers as helper
import data_preprocessing as preprocess
import multi_models_splitter as multi
import implementations as imp

# Load training data
y_train, tx_train, _ = helper.load_csv_data('../all/train.csv')

# Placeholders (TODO: fill arrays with real values)
degrees = [1, 2, 3, 4]
lambdas = [1, 2, 3, 4]
k_cross_val = [1, 2, 3, 4]

# Best results
best_preds = np.ones( (y_train.shape[0] , 1) )
best_pred_error = 1.0
best_weights = np.array()
best_cat_values = np.array()

# Best parameters
best_degree = 0
best_lambda = 0.0
best_k = 0

# Remove outliers
preprocess.outliers_to_mean(tx_train)

for degree in degrees: # For each degree...
    processed_tx_train = preprocess.build_poly(tx_train, degree)[:,1:]
    for lambda_ in lambdas: # For each lambda...
        for k in k_cross_val: # For each k...

            # Use the multi_models_splitter function to compute our model 
            y_pred, pred_error, cat_values, weights = multi.multi_models_splitter(y_train, processed_tx_train, 22, k, imp.ridge_regression, [lambda_])
            
            if pred_error < best_pred_error:
                # Update best rsults
                best_pred_error = pred_error
                best_preds = np.copy(y_pred)
                best_weights = weights
                best_cat_values = cat_values

                # Update best parameters
                best_degree = degree
                best_lambda = lambda_
                best_k = k

print("Best prediction error on training data is " + str(best_pred_error))
print("It was obtained with parameters (degree, lambda, k) = (" + best_degree + ", " + best_lambda + ", " + best_k + ")")

# Load test data
_, tx_test, ids = helper.load_csv_data('../all/test.csv')

# Remove outliers and do pre-processing
preprocess.outliers_to_mean(tx_test)
processed_tx_test = preprocess.build_poly(tx_train, best_degree)[:,1:]

# Use the multi_models_splitter function to compute our model 
y_pred_test = multi.make_predictions_from_weights(tx_test, 22, best_weights, best_cat_values) 

# Save the predictions
filename = 'results/integration0.csv'
helper.create_csv_submission(ids, y_pred, filename)
