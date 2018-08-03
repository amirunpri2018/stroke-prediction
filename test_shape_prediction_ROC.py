import datetime
from tester.CaeReconstructionTesterROC import CaeReconstructionTesterROC
from common.model.Cae3D import Cae3D, Dec3D, Enc3D
from common import data, util


def test():
    args = util.get_args_shape_testing()

    assert len(args.fold) == len(args.path), 'You must provide as many --fold arguments as caepath model arguments\
                                                in the exact same order!'

    # Params / Config
    modalities = ['_CBV_reg1_downsampled', '_TTD_reg1_downsampled']
    labels = ['_CBVmap_subset_reg1_downsampled', '_TTDmap_subset_reg1_downsampled',
              '_FUCT_MAP_T_Samplespace_subset_reg1_downsampled']
    channels_cae = args.channelscae
    n_globals = args.globals  # type(core/penu), tO_to_tA, NHISS, sex, age
    resample_size = int(args.xyoriginal * args.xyresample)
    normalization_hours_penumbra = args.normalize
    steps = range(6)  # fixed steps for tAdmission-->tReca: 0-5 hrs
    pad = args.padding
    pad_value = 0
    leakage = 0.2
    cuda = True

    # Unet model
    enc = Enc3D(size_input_xy=resample_size, size_input_z=args.zsize,
                channels=channels_cae, n_ch_global=n_globals, leakage=leakage)
    dec = Dec3D(size_input_xy=resample_size, size_input_z=args.zsize,
                channels=channels_cae, n_ch_global=n_globals, leakage=leakage)
    cae = Cae3D(enc, dec)
    if cuda:
        cae = cae.cuda()

    # Data
    transform = [data.ResamplePlaneXY(args.xyresample),
                 data.PadImages(pad[0], pad[1], pad[2], pad_value=pad_value),
                 data.ToTensor()]

    # Fold-wise evaluation according to fold indices and fold model for all folds and model path provided as arguments:
    for i, path in enumerate(args.path):
        print('Model ' + path + ' of fold ' + str(i+1) + '/' + str(len(args.fold)) + ' with indices: ' + str(args.fold[i]))
        ds_test = data.get_testdata(modalities=modalities, labels=labels, transform=transform, indices=args.fold[i])
        print('Size test set:', len(ds_test.sampler.indices), '| # batches:', len(ds_test))
        # Single case evaluation for all cases in fold
        tester = CaeReconstructionTesterROC(ds_test, cae, path, args.outbasepath, normalization_hours_penumbra, steps)
        tester.run_inference()


if __name__ == '__main__':
    print(datetime.datetime.now())
    test()
    print(datetime.datetime.now())
