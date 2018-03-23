import json
import os
import time

from trainer.backend import dataset_utils
from trainer.backend.tf import train


def train_model(network_config_file, dataset_dir,
                learning_rate, metrics, loss, optimizer,
                desired_image_height, desired_image_width,
                charset_file, labels_delimiter=' ',
                max_label_length=120, num_epochs=1,
                batch_size=1, checkpoint_epochs=1):
    params = json.load(open(network_config_file, 'r'))
    labels_file = os.path.join(dataset_dir, "labels.txt")
    image_paths, labels = dataset_utils.read_dataset_list(
        labels_file, delimiter=labels_delimiter)
    images = dataset_utils.read_images(data_dir=dataset_dir,
                                       image_paths=image_paths,
                                       image_extension='png')
    images = dataset_utils.resize(images,
                                  desired_height=desired_image_height,
                                  desired_width=desired_image_width)
    images = dataset_utils.binarize(images)
    images = dataset_utils.invert(images)
    classes = dataset_utils.get_characters_from(charset_file)
    images = dataset_utils.images_as_float32(images)
    labels = dataset_utils.encode(labels, classes)
    num_classes = len(classes) + 1
    labels = dataset_utils.pad(labels, max_label_length=max_label_length)

    filename, _ = os.path.splitext(network_config_file)
    model_name = filename.split('/')[-1]

    checkpoint_dir = "checkpoint/" + str(model_name) + "_" + time.strftime("%Y%m%d-%H%M%S")

    params["learning_rate"] = learning_rate
    params["optimizer"] = optimizer
    params["metrics"] = metrics
    params["loss"] = loss

    train(params=params,
          features=images,
          labels=labels,
          num_classes=num_classes,
          checkpoint_dir=checkpoint_dir,
          batch_size=batch_size,
          num_epochs=num_epochs,
          save_checkpoint_every_n_epochs=checkpoint_epochs)
