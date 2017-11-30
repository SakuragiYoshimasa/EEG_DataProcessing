'''
Caluculation Phase locking factor and nonparametric testing.
Referenced 'Oscillatory gamma-band (30-70 Hz) activity induced by a visual search task in humans' (Tallon et al (1997))
Please see the document if you want more details.
'''

import numpy as np
from pyplfv.data_structures import EEGData
from pyplfv.utility import load_intermediate_data
from pyplfv.utility import save_intermediate_data

'''
To test whether an activity is significantly phase-locked to stimulus onset,
a statistical test (Rayleigh test) of uniformity of angle is used (Jervis et al., 1983)
http://q-bio.jp/images/5/53/角度統計配布_qbio4th.pdf
http://www.neurophys.wisc.edu/comp/docs/not011/not011.html
https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.stats.rayleigh.html
http://webspace.ship.edu/pgmarr/Geo441/Lectures/Lec%2016%20-%20Directional%20Statistics.pdf

R := The averaged
Z := n * (R^2)
'''

def rayleigh_p(Z, n):
    Z_2 = np.power(Z, 2.0)
    Z_3 = np.power(Z, 3.0)
    Z_4 = np.power(Z, 4.0)
    n_2 = np.power(n, 2.0)
    f_term = 1.0
    s_term = (2.0 * Z - Z_2) / (4.0 * n)
    t_term  = (24.0 * Z - 132.0 * Z_2 + 76.0 * Z_3 - 9.0 * Z_4) / (288.0 * n_2)
    return  np.exp(-Z) * (f_term + s_term - t_term)

'''
Pi as averaged across single trials
Leadning to a complex value describing the phase distribution of the time-frew region centered on t and f0
start_time_of_trials : the index of start timing of trials on signal array
offset: How many frame are considered to have relevant with trials before that.
length: How many frame are considered to have relevant with trials.

plf returns the normalized_tve_average and p values about it.
'''

def plf(signal, time_interval, f0, start_time_of_trials, offset, length, debug=False):

    sigma_f, sigma_t, wavelet_duration, A = gen_parameters(f0)
    normalized_tve_average = np.zeros(length, dtype='complex128')

    for trial in start_time_of_trials:
        sig = signal[trial + offset : trial + offset + length]
        normalized_tve_average += normalized_tve(sig, time_interval, f0) / len(start_time_of_trials)

    ## testing these p value
    p_arr = []
    n = len(start_time_of_trials)
    for i in range(length):
        R = np.abs(normalized_tve_average[i])
        Z = n * np.power(R, 2.0)
        p = rayleigh_p(Z, n)
        p_arr.append(p)

    return [np.abs(normalized_tve_average), np.array(p_arr)]

def plf_with_farray(signal, time_interval, farray, start_time_of_trials, offset, length, debug=False):

    plf_arr, p_arr = [[], []]
    for f in farray:
        _plf, _p = plf(signal, time_interval, f, start_time_of_trials, offset, length, debug)
        plf_arr.append(_plf)
        p_arr.append(_p)
    return [plf_arr, p_arr]

def show_plf_spectgram(sig, time_interval, start_time_of_trials, farray, offset, length, show_p=False, save=False, filename='.plf.png'):

    _plf, _ps = plf_with_farray(sig,
                          time_interval,
                          farray,
                          start_time_of_trials,
                          offset,
                          length)
    import matplotlib.pyplot as plt
    if show_p:
        fig, (axu, axl) = plt.subplots(nrows=2, figsize=(10,5))
        matu =  axu.matshow(_plf)
        axu.set_title('PLF')
        axu.set_xlabel('Frame')
        axu.set_ylabel('Freq(Hz)')
        #axu.colorbar()

        matl = axl.matshow(_ps)
        axl.set_title('P values')
        axl.set_xlabel('Frame')
        axl.set_ylabel('Freq(Hz)')

        fig.subplots_adjust(right=0.8)
        cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
        fig.colorbar(matu, cbar_ax)
        if save:
            plt.savefig(filename)
        plt.show()
    else:
        plt.matshow(_plf)
        plt.colorbar()
        plt.xlabel('Frame')
        plt.ylabel('Freq')
        plt.show()
    return [np.array(_plf), np.array(_ps)]

def show_plf_spectgram_from_eeg(eeg_data, sig_name, trial_marker, farray, offset, length, show_p=False, save=False, filename='./plf.png'):
    sig = eeg_data.signals[sig_name]
    start_time_of_trials = [eeg_data.markers[i].position for i in range(len(eeg_data.markers)) if eeg_data.markers[i].description == trial_marker]
    time_interval = eeg_data.properties.sampling_interval / 1000000
    return show_plf_spectgram(sig, time_interval, start_time_of_trials, farray, offset, length, show_p, save, filename)
