from datetime import datetime

from typing import Optional

from uuid import UUID, uuid4

from sqlalchemy import (

    BigInteger,

    DateTime,

    Float,

    Index,

    String,

    Text,

    func,

)

from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PG_UUID

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ...core.constants import ForecastHorizon, PredictionStatus

class Base(DeclarativeBase):

    pass

class PredictionModel(Base):

    __tablename__ = "predictions"

    __table_args__ = (

        Index("idx_predictions_user_id", "user_id"),

        Index("idx_predictions_created_at", "created_at"),

        Index("idx_predictions_status", "status"),

    )

    id: Mapped[UUID] = mapped_column(

        PG_UUID(as_uuid=True),

        primary_key=True,

        default=uuid4,

    )

    user_id: Mapped[UUID] = mapped_column(

        PG_UUID(as_uuid=True),

        nullable=False,

        index=True,

    )

    features: Mapped[dict] = mapped_column(JSONB, nullable=False)

    predicted_price: Mapped[float] = mapped_column(Float, nullable=False)

    predicted_price_per_sqm: Mapped[float] = mapped_column(Float, nullable=False)

    horizon: Mapped[str] = mapped_column(

        String(20),

        nullable=False,

        default=ForecastHorizon.NOW.value,

    )

    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    status: Mapped[str] = mapped_column(

        String(20),

        nullable=False,

        default=PredictionStatus.SUCCESS.value,

    )

    comparables: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)

    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(

        DateTime(timezone=True),

        server_default=func.now(),

        nullable=False,

    )

    updated_at: Mapped[datetime] = mapped_column(

        DateTime(timezone=True),

        server_default=func.now(),

        onupdate=func.now(),

        nullable=False,

    )

    def __repr__(self) -> str:

        return (

            f"<Prediction id={self.id} user={self.user_id} "

            f"status={self.status} price={self.predicted_price}>"

        )
