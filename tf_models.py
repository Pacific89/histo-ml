import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Activation
import tensorboard
import itertools

def get_models(num_layers: int,
               min_nodes_per_layer: int,
               max_nodes_per_layer: int,
               node_step_size: int,
               input_shape: tuple,
               hidden_layer_activation: str = 'relu',
               num_nodes_at_output: int = 2,
               classification = True) -> list:
    """ generate different neural network architectures.
    code from: https://towardsdatascience.com/how-to-find-optimal-neural-network-architecture-with-tensorflow-the-easy-way-50575a03d060

    Parameters
    ----------
    num_layers : int
        number of layers (fixed)
    min_nodes_per_layer : int
        minimum number of nodes (units) per layer
    max_nodes_per_layer : int
        maximum number of nodes (units) per layer
    node_step_size : int
        step size for permutations
    input_shape : tuple
        data input shape (e.g.: (512,) for 512 SimCLR features)
    hidden_layer_activation : str, optional
        activation function for hidden layers, by default 'relu'
    num_nodes_at_output : int, optional
        number of output units, by default 2
    classification : bool, optional
        if classification is used, the outputfunction is different: either "softmax" or "sigmoid", by default True

    Returns
    -------
    [List]
        list of keras models
    """
    
    if classification:
        output_layer_activation: str = 'softmax'
    else:
        output_layer_activation: str = 'sigmoid'

    node_options = list(range(min_nodes_per_layer, max_nodes_per_layer + 1, node_step_size))
    layer_possibilities = [node_options] * num_layers
    layer_node_permutations = list(itertools.product(*layer_possibilities))
    
    models = []
    for permutation in layer_node_permutations:
        model = tf.keras.Sequential()
        model.add(tf.keras.layers.InputLayer(input_shape=input_shape))
        model_name = ''

        for nodes_at_layer in permutation:
            model.add(tf.keras.layers.Dense(nodes_at_layer, activation=hidden_layer_activation))
            model_name += f'dense{nodes_at_layer}_'

        model.add(tf.keras.layers.Dense(num_nodes_at_output, activation=output_layer_activation))
        model._name = model_name[:-1]
        models.append(model)
        
    return models

def get_tensorboard_callback(log_dir="./logs"):
    """creates callback for the training loops to store accuracy metrics for tensorboard
    Parameters
    ----------
    log_dir : str, optional
        directory to store the logfiles, by default "./logs"

    Returns
    -------
    callback function
        keras callback function for tensoboard
    """

    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir)

    return tensorboard_callback

def _mlp_regressor(X, y, epochs=500, batch_size=200, validation_split=0.2, model=None):
    """Multilay Perceptron for Regression. [Should be same function as classification but with a different activation function in the last layer]
    Parameters
    ----------
    X : array
        training and validation data (e.g.: SimCLR features)
    y : array
        target values for regression (e.g.: Gis Score (0;100) )
    epochs : int, optional
        sets the number of epochs for training, by default 500
    batch_size : int, optional
        batch size for training, by default 200
    validation_split : float, optional
        splits the data of X and y into training and validation sets, by default 0.2
    model : tf-model, optional
        tensorflow model to test a list of different architectures, by default None
    """

    if model == None:
        model = Sequential([
        Flatten(input_shape=(512,)),
        Dense(100, activation='relu', kernel_initializer='he_normal'),
        Dense(50, activation='relu', kernel_initializer='he_normal'),
        Dense(10, activation='relu', kernel_initializer='he_normal'),
        Dense(1),
        ])
    model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])
    model.summary()

    model.fit(X, y, epochs=epochs, batch_size=batch_size, validation_split=validation_split,  callbacks=[get_tensorboard_callback()])


def _mlp_classifier(X, y, epochs=500, batch_size=200, validation_split=0.2, model=None):
    """Multi Layer Perceptron classifier with some adjustable hyperparemeters.
    Either the model is provided or some default model is built.

    Parameters
    ----------
    X : array
        training and validation data (e.g.: SimCLR features)
    y : array
        target values for classification (e.g.: HRD Pos | Neg: 0 | 1)
    epochs : int, optional
        sets the number of epochs for training, by default 500
    batch_size : int, optional
        batch size for training, by default 200
    validation_split : float, optional
        splits the data of X and y into training and validation sets, by default 0.2
    model : tf-model, optional
        tensorflow model to test a list of different architectures, by default None
    """

    if model == None:
        model = Sequential([
        Flatten(input_shape=(512,)),
        Dense(512, activation='relu'),
        Dense(128, activation='relu'),
        Dense(64, activation='relu'), 
        Dense(64, activation='relu'), 
        Dense(32, activation='relu'),
        Dense(2, activation='softmax'), 
        ])

    ckpt = tf.train.Checkpoint(model)
    manager = tf.train.CheckpointManager(ckpt, './tf_ckpts', max_to_keep=3)

    model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

    model.summary()
    model.fit(X, y, epochs=epochs, batch_size=batch_size, validation_split=validation_split, callbacks=[get_tensorboard_callback()])

    save_path = manager.save()
    print("Saved to: ", save_path)



if __name__ == "__main__":
    """ main function just for some minor tests
    printing all models that are generated by the get_models function
    """

    print([m.summary() for m in get_models(4, 32, 192, 32, 512)])