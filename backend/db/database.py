from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


async def init_db():
    # Import all models to ensure they are registered with Base
    from models.claim_models import Claim
    from models.workflow_models import WorkflowLog, AgentResult
    from models.metrics_models import ProcessingMetrics
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
