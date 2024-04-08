from collections import defaultdict
from typing import Optional, List

import pandas as pd
from fastapi import File, UploadFile, HTTPException
from sqlmodel import Session, select

from src import engine
from src.api.database.schemas import IntersectionsInput
from src.models import Client, Affiliate


async def api_upload_database(
        department_id: Optional[int] = None,
        desk_id: Optional[int] = None,
        responsible_id: Optional[int] = None,
        affiliate_id: Optional[int] = None,
        new_affiliate_name: Optional[str] = None,
        funnel_name: Optional[str] = None,
        file=File(...)
):
    contents = await file.read()
    df = pd.read_excel(contents)
    df.columns = df.columns.str.lower()

    duplicates = []
    new_records_count = 0
    if affiliate_id is None and new_affiliate_name is None:
        raise HTTPException(status_code=400, detail="give affiliate id or affiliate name for new affiliate")

    if affiliate_id is not None and new_affiliate_name is not None:
        raise HTTPException(status_code=400, detail="make a choice: new affiliate or existing")

    new_affiliate = None
    if new_affiliate_name:
        with Session(engine) as session:
            new_affiliate = Affiliate(name=new_affiliate_name)
            session.add(new_affiliate)
            session.commit()
            session.refresh(new_affiliate)

    with Session(engine) as session:
        for index, row in df.iterrows():
            statement = select(Client).where((Client.email == row['email']) | (Client.phone_number == str(row['phone_number'])))
            existing_client = session.exec(statement).first()
            if existing_client:
                duplicates.append(existing_client)
            else:
                client = Client(
                    department_id=department_id,
                    desk_id=desk_id,
                    responsible_id=responsible_id,
                    email=row['email'],
                )
                if new_affiliate:
                    client.affiliate_id = new_affiliate.id
                elif affiliate_id:
                    client.affiliate_id = affiliate_id
                else:
                    raise HTTPException(status_code=400, detail="must be given affiliate_id or affiliate_name")

                if 'first_name' in df.columns:
                    client.first_name = row['first_name']
                if 'second_name' in df.columns:
                    client.second_name = row['second_name']
                if 'name' in df.columns:
                    client.first_name, client.second_name = row['name'].split(' ', 1)
                elif 'first_name' not in df.columns and 'second_name' not in df.columns and 'name' not in df.columns:
                    raise HTTPException(status_code=400, detail="At least one of 'first_name', 'second_name', or 'name' must be present in the DataFrame columns.")

                if 'email' in df.columns:
                    client.email = row['email']
                else:
                    raise HTTPException(status_code=400, detail="email not found")

                if 'phone_number' in df.columns:
                    client.phone_number = row['phone_number']
                elif 'phone' in df.columns:
                    client.phone_number = row['phone']
                else:
                    raise ValueError("Neither 'phone_number' nor 'phone' found")

                if 'funnel_name' in df.columns:
                    client.funnel_name = row['funnel_name']
                elif 'aff_funnel' in df.columns:
                    client.funnel_name = row['aff_funnel']
                elif funnel_name is not None:
                    client.funnel_name = funnel_name
                else:
                    raise HTTPException(status_code=400, detail="phone not found")

                if 'description' in df.columns:
                    client.description = row['description']
                if 'comment' in df.columns:
                    client.description = row['comment']

                session.add(client)
                new_records_count += 1
        session.commit()

        clients_affiliate_id = defaultdict(int)

        for client in duplicates:
            affiliate_id = client.affiliate_id
            clients_affiliate_id[affiliate_id] += 1

        duplicates_emails = [client.email for client in duplicates] if duplicates is not None else []

        return {
            "new_records_count": new_records_count,
            "duplicates_count": len(duplicates_emails),
            "duplicates": duplicates_emails,
            "duplicates_by_affiliate_id": clients_affiliate_id
        }


async def api_check_database(
        # exclude_affiliate_ids: Optional[List[int]] = None,
        file=File(...)
    ):
    contents = await file.read()
    df = pd.read_excel(contents)

    if 'email' not in df.columns:
        if len(df.columns) != 1:
            raise HTTPException(status_code=400, detail="not found email column")
        df.insert(0, 'email', '')

    df.columns = df.columns.str.lower()

    duplicates = []
    unique = []

    with Session(engine) as session:
        for index, row in df.iterrows():
            statement = select(Client).where(
                (Client.email == row['email']))
            existing_client = session.exec(statement).first()
            if existing_client:
                duplicates.append(existing_client)
            else:
                unique.append(row['email'])

        clients_affiliate_id = defaultdict(int)

        for client in duplicates:
            affiliate_id = client.affiliate_id
            clients_affiliate_id[affiliate_id] += 1

        unique_emails = [client for client in unique] if unique is not None else []
        duplicates_emails = [client.email for client in duplicates] if duplicates is not None else []

        total_count = df.shape[0]

        return {
            "given_count": total_count,
            "unique_count": len(unique_emails),
            "unique": unique_emails,
            "duplicates_count": len(duplicates_emails),
            "duplicates": duplicates_emails,
            "duplicates_by_affiliate_id": clients_affiliate_id
        }


