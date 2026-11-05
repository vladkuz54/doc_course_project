"use client";

import {
  Fragment,
  useEffect,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { apiDelete, apiGet, apiPost, apiPut } from "../api";
import { DateField, toIsoDate } from "../shared/DateField";
import { formatDate, type Vehicle } from "../shared/fleet";
import { FormRow } from "../shared/FormRow";
import { Messages } from "../shared/Messages";
import { StatusSections } from "../shared/StatusSections";
import { useData } from "../shared/useData";

type FuelRecord = {
  id: number;
  vehicle_id: number;
  date: string;
  amount: string;
  liters: number;
};

type InsurancePolicy = {
  id: number;
  vehicle_id: number;
  date: string;
  amount: string;
  start_date: string;
  end_date: string;
};

type RepairType = "SERVICE_TO" | "INSPECTION" | "REPAIR";

type RepairRecord = {
  id: number;
  vehicle_id: number;
  date: string;
  amount: string | null;
  type: RepairType;
  description: string;
  status: "PLANNED" | "DONE";
};

const REPAIR_TYPE_LABELS: Record<RepairType, string> = {
  SERVICE_TO: "Service",
  INSPECTION: "Inspection",
  REPAIR: "Repair",
};

const TABS = {
  fuel: { label: "Fuel", Tab: FuelTab },
  repairs: { label: "Repairs", Tab: RepairsTab },
  insurance: { label: "Insurance", Tab: InsuranceTab },
};

type TabName = keyof typeof TABS;

const REPAIR_SECTIONS: { status: RepairRecord["status"]; label: string }[] = [
  { status: "PLANNED", label: "Planned" },
  { status: "DONE", label: "Done" },
];

function withVehicles<T>(path: string) {
  return () =>
    Promise.all([apiGet<T[]>(path), apiGet<Vehicle[]>("/vehicles/")]);
}

const loadFuel = withVehicles<FuelRecord>("/fuel-records/");
const loadRepairs = withVehicles<RepairRecord>("/repair-records/");
const loadInsurance = withVehicles<InsurancePolicy>("/insurance-policies/");

function newestFirst(a: { date: string }, b: { date: string }) {
  return b.date.localeCompare(a.date);
}

export function AccountingPage() {
  const [tab, setTab] = useState<TabName>("fuel");
  const { Tab } = TABS[tab];

  return (
    <>
      <h1>Accounting</h1>
      <div className="tabs" role="tablist">
        {(Object.keys(TABS) as TabName[]).map((name) => (
          <button
            key={name}
            type="button"
            role="tab"
            aria-selected={name === tab}
            className={name === tab ? undefined : "secondary"}
            onClick={() => setTab(name)}
          >
            {TABS[name].label}
          </button>
        ))}
      </div>
      <Tab key={tab} />
    </>
  );
}

function useRecords<T, E>(load: () => Promise<[T[], Vehicle[]]>) {
  const { data, error, notice, pending, run, clearMessages } = useData(load);
  const [editing, setEditing] = useState<E | "new" | null>(null);

  useEffect(() => {
    if (editing === "new") window.scrollTo(0, 0);
  }, [editing]);

  const openForm = (next: E | "new" | null) => {
    clearMessages();
    setEditing(next);
  };

  const save = (action: () => Promise<unknown>, doneNotice: string) => {
    run(action, doneNotice).then((saved) => {
      if (saved) setEditing(null);
    });
  };

  const remove = (path: string, doneNotice: string) => {
    if (window.confirm("Delete this record?")) {
      run(() => apiDelete(path), doneNotice);
    }
  };

  const [records, vehicles] = data ?? [];
  const vehicleName = (id: number) =>
    vehicles?.find((vehicle) => vehicle.id === id)?.make;

  return {
    records,
    run,
    clearMessages,
    vehicles: vehicles ?? [],
    vehicleName,
    error,
    notice,
    pending,
    editing,
    openForm,
    save,
    remove,
  };
}

function RecordForm({
  title,
  saveLabel,
  pending,
  onSubmit,
  onCancel,
  children,
}: {
  title: string;
  saveLabel: string;
  pending: boolean;
  onSubmit: (form: FormData) => void;
  onCancel: () => void;
  children: ReactNode;
}) {
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit(new FormData(event.currentTarget));
  };

  return (
    <form className="panel" onSubmit={submit}>
      <h2 className="panel-title">{title}</h2>
      {children}
      <div className="form-actions">
        <button type="submit" disabled={pending}>
          {saveLabel}
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function VehicleSelect({
  vehicles,
  defaultValue,
}: {
  vehicles: Vehicle[];
  defaultValue?: number;
}) {
  return (
    <label>
      Vehicle
      <select name="vehicle_id" defaultValue={defaultValue} required>
        {vehicles.map((vehicle) => (
          <option key={vehicle.id} value={vehicle.id}>
            {vehicle.make}
          </option>
        ))}
      </select>
    </label>
  );
}

function NumberField({
  label,
  name,
  defaultValue,
}: {
  label: string;
  name: string;
  defaultValue?: string | number;
}) {
  return (
    <label>
      {label}
      <input
        name={name}
        type="number"
        step="any"
        defaultValue={defaultValue}
        required
      />
    </label>
  );
}

function RowActions({
  pending,
  onEdit,
  onDelete,
  children,
}: {
  pending: boolean;
  onEdit: () => void;
  onDelete: () => void;
  children?: ReactNode;
}) {
  return (
    <td className="actions">
      {children}
      <button type="button" className="secondary" onClick={onEdit}>
        Edit
      </button>
      <button
        type="button"
        className="secondary danger"
        disabled={pending}
        onClick={onDelete}
      >
        Delete
      </button>
    </td>
  );
}

function dateOf(form: FormData, name: string) {
  return toIsoDate(String(form.get(name)));
}

function FuelTab() {
  const records = useRecords<FuelRecord, FuelRecord>(loadFuel);
  const { editing, openForm, save, remove, pending, vehicles } = records;

  const fields = (form: FormData) => ({
    vehicle_id: Number(form.get("vehicle_id")),
    date: dateOf(form, "date"),
    amount: Number(form.get("amount")),
    liters: Number(form.get("liters")),
  });

  const submit = (form: FormData) =>
    save(
      () =>
        editing && editing !== "new"
          ? apiPut(`/fuel-records/${editing.id}`, fields(form))
          : apiPost("/fuel-records/", fields(form)),
      "Fuel record saved.",
    );

  const record = editing && editing !== "new" ? editing : null;

  const form = editing && (
    <RecordForm
      key={record?.id ?? "new"}
      title={record ? "Edit fuel record" : "New fuel record"}
      saveLabel="Save record"
      pending={pending}
      onSubmit={submit}
      onCancel={() => openForm(null)}
    >
      <VehicleSelect vehicles={vehicles} defaultValue={record?.vehicle_id} />
      <label>
        Date
        <DateField name="date" defaultValue={record?.date} required />
      </label>
      <NumberField label="Amount" name="amount" defaultValue={record?.amount} />
      <NumberField label="Liters" name="liters" defaultValue={record?.liters} />
    </RecordForm>
  );

  return (
    <>
      <div className="tab-actions">
        <button type="button" onClick={() => openForm("new")}>
          Add fuel record
        </button>
      </div>
      <Messages
        error={records.error}
        notice={records.notice}
        onClose={records.clearMessages}
      />
      {editing === "new" && form}
      {records.records?.length === 0 && (
        <p className="muted">No fuel records yet.</p>
      )}
      {records.records && records.records.length > 0 && (
        <div className="table-box">
          <table>
            <thead>
              <tr>
                <th>Vehicle</th>
                <th>Date</th>
                <th>Amount</th>
                <th>Liters</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {records.records.toSorted(newestFirst).map((row) => (
                <Fragment key={row.id}>
                  <tr>
                    <td>{records.vehicleName(row.vehicle_id)}</td>
                    <td>{formatDate(row.date)}</td>
                    <td>{row.amount}</td>
                    <td>{row.liters}</td>
                    <RowActions
                      pending={pending}
                      onEdit={() => openForm(row)}
                      onDelete={() =>
                        remove(
                          `/fuel-records/${row.id}`,
                          "Fuel record deleted.",
                        )
                      }
                    />
                  </tr>
                  {record?.id === row.id && (
                    <FormRow colSpan={5}>{form}</FormRow>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function InsuranceTab() {
  const records = useRecords<InsurancePolicy, InsurancePolicy>(loadInsurance);
  const { editing, openForm, save, remove, pending, vehicles } = records;

  const fields = (form: FormData) => ({
    vehicle_id: Number(form.get("vehicle_id")),
    date: dateOf(form, "date"),
    amount: Number(form.get("amount")),
    start_date: dateOf(form, "start_date"),
    end_date: dateOf(form, "end_date"),
  });

  const submit = (form: FormData) =>
    save(
      () =>
        editing && editing !== "new"
          ? apiPut(`/insurance-policies/${editing.id}`, fields(form))
          : apiPost("/insurance-policies/", fields(form)),
      "Insurance policy saved.",
    );

  const record = editing && editing !== "new" ? editing : null;

  const form = editing && (
    <RecordForm
      key={record?.id ?? "new"}
      title={record ? "Edit insurance policy" : "New insurance policy"}
      saveLabel="Save policy"
      pending={pending}
      onSubmit={submit}
      onCancel={() => openForm(null)}
    >
      <VehicleSelect vehicles={vehicles} defaultValue={record?.vehicle_id} />
      <label>
        Payment date
        <DateField name="date" defaultValue={record?.date} required />
      </label>
      <NumberField label="Amount" name="amount" defaultValue={record?.amount} />
      <label>
        Cover starts
        <DateField
          name="start_date"
          defaultValue={record?.start_date}
          required
        />
      </label>
      <label>
        Cover ends
        <DateField name="end_date" defaultValue={record?.end_date} required />
      </label>
    </RecordForm>
  );

  return (
    <>
      <div className="tab-actions">
        <button type="button" onClick={() => openForm("new")}>
          Add insurance policy
        </button>
      </div>
      <Messages
        error={records.error}
        notice={records.notice}
        onClose={records.clearMessages}
      />
      {editing === "new" && form}
      {records.records?.length === 0 && (
        <p className="muted">No insurance policies yet.</p>
      )}
      {records.records && records.records.length > 0 && (
        <div className="table-box">
          <table>
            <thead>
              <tr>
                <th>Vehicle</th>
                <th>Payment date</th>
                <th>Amount</th>
                <th>Cover starts</th>
                <th>Cover ends</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {records.records.toSorted(newestFirst).map((row) => (
                <Fragment key={row.id}>
                  <tr>
                    <td>{records.vehicleName(row.vehicle_id)}</td>
                    <td>{formatDate(row.date)}</td>
                    <td>{row.amount}</td>
                    <td>{formatDate(row.start_date)}</td>
                    <td>{formatDate(row.end_date)}</td>
                    <RowActions
                      pending={pending}
                      onEdit={() => openForm(row)}
                      onDelete={() =>
                        remove(
                          `/insurance-policies/${row.id}`,
                          "Insurance policy deleted.",
                        )
                      }
                    />
                  </tr>
                  {record?.id === row.id && (
                    <FormRow colSpan={6}>{form}</FormRow>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function RepairsTab() {
  const records = useRecords<RepairRecord, RepairRecord>(loadRepairs);
  const { editing, openForm, save, remove, pending, vehicles } = records;
  const [costing, setCosting] = useState<RepairRecord | null>(null);

  const open = (next: RepairRecord | "new" | null) => {
    setCosting(null);
    openForm(next);
  };

  const openCost = (repair: RepairRecord) => {
    openForm(null);
    setCosting(repair);
  };

  const shared = (form: FormData) => ({
    date: dateOf(form, "date"),
    type: form.get("type"),
    description: form.get("description"),
  });

  const add = (form: FormData) =>
    save(
      () =>
        apiPost("/repair-records/", {
          ...shared(form),
          vehicle_id: Number(form.get("vehicle_id")),
          status: form.get("status"),
          amount:
            form.get("status") === "DONE" ? Number(form.get("amount")) : null,
        }),
      "Repair saved.",
    );

  const update = (repair: RepairRecord, form: FormData) =>
    save(
      () =>
        apiPut(`/repair-records/${repair.id}`, {
          ...shared(form),
          vehicle_id: repair.vehicle_id,
          status: repair.status,
          amount: repair.amount,
        }),
      "Repair saved.",
    );

  const recordCost = (repair: RepairRecord, form: FormData) =>
    records
      .run(
        () =>
          apiPost(`/repair-records/${repair.id}/cost`, {
            cost: Number(form.get("cost")),
          }),
        "Repair cost recorded.",
      )
      .then((saved) => {
        if (saved) setCosting(null);
      });

  const editingRepair = editing && editing !== "new" ? editing : null;

  const costForm = costing && (
    <RecordForm
      key={`cost-${costing.id}`}
      title={`Record the cost of ${REPAIR_TYPE_LABELS[costing.type].toLowerCase()}, ${records.vehicleName(costing.vehicle_id)}`}
      saveLabel="Record cost"
      pending={pending}
      onSubmit={(form) => recordCost(costing, form)}
      onCancel={() => open(null)}
    >
      <NumberField label="Cost" name="cost" />
    </RecordForm>
  );

  const editForm = editingRepair && (
    <RecordForm
      key={editingRepair.id}
      title={`Edit repair of ${records.vehicleName(editingRepair.vehicle_id)}`}
      saveLabel="Save repair"
      pending={pending}
      onSubmit={(form) => update(editingRepair, form)}
      onCancel={() => open(null)}
    >
      <RepairFields repair={editingRepair} />
    </RecordForm>
  );

  return (
    <>
      <div className="tab-actions">
        <button type="button" onClick={() => open("new")}>
          Add repair
        </button>
      </div>
      <Messages
        error={records.error}
        notice={records.notice}
        onClose={records.clearMessages}
      />
      {editing === "new" && (
        <NewRepairForm
          vehicles={vehicles}
          pending={pending}
          onSubmit={add}
          onCancel={() => open(null)}
        />
      )}
      {records.records?.length === 0 && (
        <p className="muted">No repairs yet.</p>
      )}
      {records.records && records.records.length > 0 && (
        <StatusSections
          items={records.records.toSorted(newestFirst)}
          statusOf={(row) => row.status}
          sections={REPAIR_SECTIONS}
        >
          {(rows) => (
            <table>
              <thead>
                <tr>
                  <th>Vehicle</th>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Description</th>
                  {rows[0].status === "DONE" && <th>Cost</th>}
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <Fragment key={row.id}>
                    <tr>
                      <td>{records.vehicleName(row.vehicle_id)}</td>
                      <td>{formatDate(row.date)}</td>
                      <td>{REPAIR_TYPE_LABELS[row.type]}</td>
                      <td>{row.description}</td>
                      {row.status === "DONE" && <td>{row.amount}</td>}
                      <RowActions
                        pending={pending}
                        onEdit={() => open(row)}
                        onDelete={() =>
                          remove(`/repair-records/${row.id}`, "Repair deleted.")
                        }
                      >
                        {row.status === "PLANNED" && (
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => openCost(row)}
                          >
                            Record cost
                          </button>
                        )}
                      </RowActions>
                    </tr>
                    {editingRepair?.id === row.id && (
                      <FormRow colSpan={row.status === "DONE" ? 6 : 5}>
                        {editForm}
                      </FormRow>
                    )}
                    {costing?.id === row.id && (
                      <FormRow colSpan={row.status === "DONE" ? 6 : 5}>
                        {costForm}
                      </FormRow>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          )}
        </StatusSections>
      )}
    </>
  );
}

function RepairFields({ repair }: { repair?: RepairRecord }) {
  return (
    <>
      <label>
        Date
        <DateField name="date" defaultValue={repair?.date} required />
      </label>
      <label>
        Type
        <select name="type" defaultValue={repair?.type}>
          {Object.entries(REPAIR_TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label>
        Description
        <input name="description" defaultValue={repair?.description} />
      </label>
    </>
  );
}

function NewRepairForm({
  vehicles,
  pending,
  onSubmit,
  onCancel,
}: {
  vehicles: Vehicle[];
  pending: boolean;
  onSubmit: (form: FormData) => void;
  onCancel: () => void;
}) {
  const [status, setStatus] = useState<RepairRecord["status"]>("PLANNED");

  return (
    <RecordForm
      title="New repair"
      saveLabel="Save repair"
      pending={pending}
      onSubmit={onSubmit}
      onCancel={onCancel}
    >
      <label>
        Status
        <select
          name="status"
          value={status}
          onChange={(event) =>
            setStatus(event.target.value as RepairRecord["status"])
          }
        >
          <option value="PLANNED">Planned</option>
          <option value="DONE">Done</option>
        </select>
      </label>
      <VehicleSelect
        vehicles={
          status === "PLANNED"
            ? vehicles.filter((vehicle) => vehicle.status === "ACTIVE")
            : vehicles
        }
      />
      <RepairFields />
      {status === "DONE" && <NumberField label="Cost" name="amount" />}
    </RecordForm>
  );
}
