from common.dto.Dto import Dto
from common.inference.Inference import Inference
from common.dto.MetricMeasuresDto import MetricMeasuresDto
import common.dto.MetricMeasuresDto as MetricMeasuresDtoInit
from torch.utils.data import DataLoader
from torch.nn import Module
import torch


class Tester(Inference):
    """Base class with a standard routine for
    a testing procedure. The single steps can
    be overridden by subclasses to specify the
    procedures required for a specific test run.
    """

    def __init__(self, dataloader: DataLoader, model: Module, path_model: str, path_outputs_base: str='/tmp/'):
        Inference.__init__(self, model, path_model, path_outputs_base)
        assert dataloader.batch_size == 1, "You must ensure a batch size of 1 for correct case metric measures."
        self._dataloader = dataloader
        self._path_outputs_base = path_outputs_base
        self._model = model
        self._model.load_state_dict(torch.load(path_model))
        for p in self._model.parameters():
            p.requires_grad = False
        self._model.eval()

    def infer_batch(self, batch: dict):
        dto = self.inference_step(batch)
        batch_metrics = self.batch_metrics_step(dto)
        self.save_inference(dto, batch)
        return batch_metrics, dto

    def batch_metrics_step(self, dto: Dto):
        return MetricMeasuresDtoInit.init_dto()

    def save_inference(self, dto: Dto, batch: dict):
        pass

    def print_inference(self, batch: dict, metrics: MetricMeasuresDto, dto: Dto = None):
        pass

    def run_inference(self):
        for batch in self._dataloader:
            batch_metrics, dto = self.infer_batch(batch)
            self.print_inference(batch, batch_metrics, dto)
