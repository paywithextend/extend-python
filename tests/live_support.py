"""Live-test cleanup and reconciliation records; contains no credentials."""
import asyncio
import json
import os
import uuid
from contextlib import AsyncExitStack


class LiveRun:
    def __init__(self, sdk, config, directory):
        self.sdk = sdk
        self.config = config
        self.directory = directory
        self.name = "sdk-test-" + uuid.uuid4().hex[:12]
        self.stack = AsyncExitStack()
        self.records = []
        self.journal = directory / (self.name + ".json")

    async def __aenter__(self):
        await self.stack.__aenter__()
        return self

    async def __aexit__(self, *exc):
        return await self.stack.__aexit__(*exc)

    def _save(self):
        with open(os.open(self.journal, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as f:
            json.dump({"environment": self.config["environment"], "resources": self.records}, f, indent=2)

    def cleanup(self, kind, resource_id, callback, *args, **kwargs):
        record = {"kind": kind, "id": resource_id, "cleanup": "pending"}
        self.records.append(record)

        async def execute():
            try:
                await callback(*args, **kwargs)
            except Exception:
                record["cleanup"] = "failed"
                self._save()
                raise
            record["cleanup"] = "complete"
            self._save()

        # Register before persisting so a filesystem failure still triggers cleanup.
        self.stack.push_async_callback(execute)
        self._save()

    async def close_card(self, card_id):
        response = await self.sdk.virtual_cards.get_virtual_card_detail(card_id)
        if response["virtualCard"]["status"] != "CLOSED":
            await self.sdk.virtual_cards.close_virtual_card(card_id)
        response = await self.sdk.virtual_cards.get_virtual_card_detail(card_id)
        assert response["virtualCard"]["status"] == "CLOSED"

    async def delete_receipt(self, receipt_id):
        await self.sdk.api_client.delete("/receiptattachments/" + receipt_id)


async def wait_for_automatch(sdk, job_id, receipt_id, expected_transaction_id, timeout=60):
    """Require terminal success and the exact fixture match; pending is not success."""
    async with asyncio.timeout(timeout):
        while True:
            result = await sdk.receipt_capture.get_automatch_status(job_id)
            assert result["id"] == job_id
            tasks = result["tasks"]
            matching = [t for t in tasks if t["receiptAttachmentId"] == receipt_id]
            if matching and all(t["status"] != "PENDING" for t in matching):
                assert len(matching) == 1
                assert matching[0]["status"] == "SUCCESS"
                assert matching[0]["transactionId"] == expected_transaction_id
                return result
            await asyncio.sleep(1)
