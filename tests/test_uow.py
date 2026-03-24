import pytest

from infrastructure.database.uow import SQLUnitOfWork
from infrastructure.database.models import User


@pytest.mark.asyncio
class TestUnitOfWork:
    async def test_commit(self, session):
        uow = SQLUnitOfWork(session)
        user = await uow.users.get_or_create(999001, "commit_test")
        await uow.commit()

        found = await uow.users.get_by_telegram_id(999001)
        assert found is not None

    async def test_rollback(self, session_factory):
        async with session_factory() as session:
            uow = SQLUnitOfWork(session)
            await uow.users.get_or_create(999002, "rollback_test")
            await uow.rollback()

        # After rollback, user should not exist
        async with session_factory() as session:
            uow2 = SQLUnitOfWork(session)
            found = await uow2.users.get_by_telegram_id(999002)
            assert found is None

    async def test_context_manager_commit(self, session_factory):
        async with session_factory() as session:
            uow = SQLUnitOfWork(session)
            async with uow:
                await uow.users.get_or_create(999003, "ctx_test")

        async with session_factory() as session:
            uow2 = SQLUnitOfWork(session)
            found = await uow2.users.get_by_telegram_id(999003)
            assert found is not None

    async def test_context_manager_rollback_on_error(self, session_factory):
        async with session_factory() as session:
            uow = SQLUnitOfWork(session)
            try:
                async with uow:
                    await uow.users.get_or_create(999004, "error_test")
                    raise ValueError("test error")
            except ValueError:
                pass

        async with session_factory() as session:
            uow2 = SQLUnitOfWork(session)
            found = await uow2.users.get_by_telegram_id(999004)
            assert found is None

    async def test_has_users_and_payments(self, session):
        uow = SQLUnitOfWork(session)
        assert hasattr(uow, "users")
        assert hasattr(uow, "payments")
