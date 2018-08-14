import torch
import datetime
from learner.CaeReconstructionLearner import CaeReconstructionLearner
from common.model.Cae3D import Cae3D, Enc3D, Dec3D
from common import data, util, metrics


def train(args):
    # Params / Config
    learning_rate = 1e-3
    momentums_cae = (0.9, 0.999)
    weight_decay = 1e-5
    path_training_metrics = args.continuetraining  # --continuetraining /share/data_zoe1/lucas/Linda_Segmentations/tmp/tmp_shape_f3.json
    criterion = metrics.BatchDiceLoss([1.0])  # nn.BCELoss()
    path_saved_model = args.caepath
    channels_cae = args.channelscae
    n_globals = args.globals  # type(core/penu), tO_to_tA, NHISS, sex, age
    resample_size = int(args.xyoriginal * args.xyresample)
    pad = args.padding
    pad_value = 0
    alpha = 1.0
    cuda = True

    # CAE model
    enc = Enc3D(size_input_xy=resample_size, size_input_z=args.zsize,
                channels=channels_cae, n_ch_global=n_globals, alpha=alpha)
    dec = Dec3D(size_input_xy=resample_size, size_input_z=args.zsize,
                channels=channels_cae, n_ch_global=n_globals, alpha=alpha)
    cae = Cae3D(enc, dec)
    if cuda:
        cae = cae.cuda()

    # Model params
    params = [p for p in cae.parameters() if p.requires_grad]
    print('# optimizing params', sum([p.nelement() * p.requires_grad for p in params]),
          '/ total: cae', sum([p.nelement() for p in cae.parameters()]))

    # Optimizer with scheduler
    optimizer = torch.optim.Adam(params, lr=learning_rate, weight_decay=weight_decay, betas=momentums_cae)
    if args.lrsteps:
        scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, args.lrsteps)
    else:
        scheduler = None

    # Data
    common_transform = [data.ResamplePlaneXY(args.xyresample),
                        data.HemisphericFlipFixedToCaseId(split_id=args.hemisflipid),
                        data.PadImages(pad[0], pad[1], pad[2], pad_value=pad_value)]
    train_transform = common_transform + [data.ElasticDeform(), data.ToTensor()]
    valid_transform = common_transform + [data.ToTensor()]
    modalities = ['_CBV_reg1_downsampled', '_TTD_reg1_downsampled']  # dummy data not used to train shape reconstruction
    labels = ['_CBVmap_subset_reg1_downsampled', '_TTDmap_subset_reg1_downsampled',
              '_FUCT_MAP_T_Samplespace_subset_reg1_downsampled']
    ds_train, ds_valid = data.get_stroke_shape_training_data(modalities, labels, train_transform, valid_transform,
                                                             args.fold, args.validsetsize, batchsize=args.batchsize)
    print('Size training set:', len(ds_train.sampler.indices), 'samples | Size validation set:', len(ds_valid.sampler.indices),
          'samples | Capacity batch:', args.batchsize, 'samples')
    print('# training batches:', len(ds_train), '| # validation batches:', len(ds_valid))

    # Training
    learner = CaeReconstructionLearner(ds_train, ds_valid, cae, path_saved_model, optimizer, scheduler,
                                       n_epochs=args.epochs, path_training_metrics=path_training_metrics,
                                       path_outputs_base=args.outbasepath, criterion=criterion)
    learner.run_training()


if __name__ == '__main__':
    print(datetime.datetime.now())
    args = util.get_args_shape_training()
    train(args)
    print(datetime.datetime.now())
