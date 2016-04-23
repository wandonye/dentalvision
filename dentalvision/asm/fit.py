'''
Algorithm for matching the model to image points.

Based on (Cootes et al. 2000, p.9) and (Blanz et al., p.4).
'''
import numpy as np
from alignment.shape import Shape
from alignment.align import CoreAlign, CoreFinder


def fit(pdmodel, image_points, n=None):
    '''
    Algorithm that finds the best shape parameters that match identified
    image points.

    In: PointDistributionModel instance pdm,
        array of new image points (x1, x2, ..., xN, y1, y2,..., yN)
    Out: the pose params (Tx, Ty, s, theta) and shape parameter (c) to
        fit the model to the image
    '''
    # initialise pose parameter finder and aligner
    aligner = Aligner()
    image = Shape(image_points)
    mean = pdmodel.mean
    # find pose parameters to align with new image points
    Tx, Ty, s, theta = aligner.get_pose_parameters(mean, image)
    # align image with model
    y = aligner.invert_transform(image, Tx, Ty, 1, theta)

    # SVD on scaled eigenvectors of the model
    u, w, v = np.linalg.svd(pdmodel.scaled_eigenvectors, full_matrices=False)
    W = np.zeros((u.shape[1], v.shape[0]))

    # define weight vector n
    if not n:
        last_eigenvalue = pdmodel.eigenvalues[-1]
        n = last_eigenvalue**2 if last_eigenvalue**2 >= 0 else 0
    # calculate the shape vector
    W[:w.size, :w.size] = np.diag(w/(w**2) + n)
    c = (v.T).dot(W.T).dot(u.T).dot(y.vector)

    return (Tx, Ty, s, theta, c)


class Aligner(CoreAlign, CoreFinder):
    '''
    Alignment class that combines the alignment methods from CoreAlign and the
    transformation variable finding methods from CoreFinder.
    '''
    def get_pose_parameters(self, subject, target):
        '''
        Find the pose parameters to align shape1 with shape2.
        In: 1xC array shape1, shape2
        Out: X_t, Y_t params that define the translation,
            s, defines the scaling
            theta, defines the rotation
        '''
        # find/perform transformations
        Tx, Ty = self.find_translation(subject, target)
        # first translate before scaling and rotating
        # translated = self.translate(subject, Tx, Ty)
        # compute a and b
        a, b = self.get_transformation_parameters(subject, target)
        s = self.find_scale(a, b)
        theta = self.find_rotation_angle(a, b)

        return (Tx, Ty, s, theta)
