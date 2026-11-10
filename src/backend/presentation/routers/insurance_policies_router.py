from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.interfaces.insurance_policies_interface import IInsurancePoliciesService
from ...bll.services.insurance_policies_service import (
    InsurancePolicyData,
)
from ..dependencies import get_insurance_policies_service
from .auth import require_admin

router = APIRouter(
    prefix="/insurance-policies",
    tags=["insurance-policies"],
    dependencies=[Depends(require_admin)],
)


class InsurancePolicyResponse(InsurancePolicyData):
    id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[InsurancePolicyResponse])
async def get_all(
    service: IInsurancePoliciesService = Depends(get_insurance_policies_service),
):
    return await service.get_all()


@router.get("/{id}", response_model=InsurancePolicyResponse)
async def get_by_id(
    id: int,
    service: IInsurancePoliciesService = Depends(get_insurance_policies_service),
):
    return await service.get_by_id(id)


@router.post("/", response_model=InsurancePolicyResponse, status_code=201)
async def create(
    data: InsurancePolicyData,
    service: IInsurancePoliciesService = Depends(get_insurance_policies_service),
):
    return await service.create(data)


@router.put("/{id}", response_model=InsurancePolicyResponse)
async def update(
    id: int,
    data: InsurancePolicyData,
    service: IInsurancePoliciesService = Depends(get_insurance_policies_service),
):
    return await service.update(id, data)


@router.delete("/{id}", response_model=InsurancePolicyResponse)
async def delete(
    id: int,
    service: IInsurancePoliciesService = Depends(get_insurance_policies_service),
):
    return await service.delete(id)
