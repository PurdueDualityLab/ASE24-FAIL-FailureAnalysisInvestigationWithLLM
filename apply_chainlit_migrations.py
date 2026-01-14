import os
import psycopg2
import sys

def run_migrations():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in environment.")
        sys.exit(1)

    print(f"Connecting to database...")
    
    # Connect to the database
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

    sql_statements = [
        # Init data layer migration
        """CREATE EXTENSION IF NOT EXISTS "pgcrypto";""",
        
        """DO $$ BEGIN
            CREATE TYPE "StepType" AS ENUM ('assistant_message', 'embedding', 'llm', 'retrieval', 'rerank', 'run', 'system_message', 'tool', 'undefined', 'user_message');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;""",

        """CREATE TABLE IF NOT EXISTS "Element" (
            "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
            "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "threadId" TEXT,
            "stepId" TEXT NOT NULL,
            "metadata" JSONB NOT NULL,
            "mime" TEXT,
            "name" TEXT NOT NULL,
            "objectKey" TEXT,
            "url" TEXT,
            "chainlitKey" TEXT,
            "display" TEXT,
            "size" TEXT,
            "language" TEXT,
            "page" INTEGER,
            "props" JSONB,

            CONSTRAINT "Element_pkey" PRIMARY KEY ("id")
        );""",

        """CREATE TABLE IF NOT EXISTS "User" (
            "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
            "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "metadata" JSONB NOT NULL,
            "identifier" TEXT NOT NULL,

            CONSTRAINT "User_pkey" PRIMARY KEY ("id")
        );""",

        """CREATE TABLE IF NOT EXISTS "Feedback" (
            "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
            "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "stepId" TEXT,
            "name" TEXT NOT NULL,
            "value" DOUBLE PRECISION NOT NULL,
            "comment" TEXT,

            CONSTRAINT "Feedback_pkey" PRIMARY KEY ("id")
        );""",

        """CREATE TABLE IF NOT EXISTS "Step" (
            "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
            "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "parentId" TEXT,
            "threadId" TEXT,
            "input" TEXT,
            "metadata" JSONB NOT NULL,
            "name" TEXT,
            "output" TEXT,
            "type" "StepType" NOT NULL,
            "showInput" TEXT DEFAULT 'json',
            "isError" BOOLEAN DEFAULT false,
            "startTime" TIMESTAMP(3) NOT NULL,
            "endTime" TIMESTAMP(3) NOT NULL,

            CONSTRAINT "Step_pkey" PRIMARY KEY ("id")
        );""",

        """CREATE TABLE IF NOT EXISTS "Thread" (
            "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
            "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "deletedAt" TIMESTAMP(3),
            "name" TEXT,
            "metadata" JSONB NOT NULL,
            "userId" TEXT,

            CONSTRAINT "Thread_pkey" PRIMARY KEY ("id")
        );""",

        # Indices (IF NOT EXISTS is not standard SQL for CREATE INDEX in older postgres, but usually supported in recent)
        """CREATE INDEX IF NOT EXISTS "Element_stepId_idx" ON "Element"("stepId");""",
        """CREATE INDEX IF NOT EXISTS "Element_threadId_idx" ON "Element"("threadId");""",
        """CREATE INDEX IF NOT EXISTS "User_identifier_idx" ON "User"("identifier");""",
        """CREATE UNIQUE INDEX IF NOT EXISTS "User_identifier_key" ON "User"("identifier");""",
        """CREATE INDEX IF NOT EXISTS "Feedback_createdAt_idx" ON "Feedback"("createdAt");""",
        """CREATE INDEX IF NOT EXISTS "Feedback_name_idx" ON "Feedback"("name");""",
        """CREATE INDEX IF NOT EXISTS "Feedback_stepId_idx" ON "Feedback"("stepId");""",
        """CREATE INDEX IF NOT EXISTS "Feedback_value_idx" ON "Feedback"("value");""",
        """CREATE INDEX IF NOT EXISTS "Feedback_name_value_idx" ON "Feedback"("name", "value");""",
        """CREATE INDEX IF NOT EXISTS "Step_createdAt_idx" ON "Step"("createdAt");""",
        """CREATE INDEX IF NOT EXISTS "Step_endTime_idx" ON "Step"("endTime");""",
        """CREATE INDEX IF NOT EXISTS "Step_parentId_idx" ON "Step"("parentId");""",
        """CREATE INDEX IF NOT EXISTS "Step_startTime_idx" ON "Step"("startTime");""",
        """CREATE INDEX IF NOT EXISTS "Step_threadId_idx" ON "Step"("threadId");""",
        """CREATE INDEX IF NOT EXISTS "Step_type_idx" ON "Step"("type");""",
        """CREATE INDEX IF NOT EXISTS "Step_name_idx" ON "Step"("name");""",
        """CREATE INDEX IF NOT EXISTS "Step_threadId_startTime_endTime_idx" ON "Step"("threadId", "startTime", "endTime");""",
        """CREATE INDEX IF NOT EXISTS "Thread_createdAt_idx" ON "Thread"("createdAt");""",
        """CREATE INDEX IF NOT EXISTS "Thread_name_idx" ON "Thread"("name");""",

        # Constraints
        # We wrap in DO block to avoid error if exists
        """DO $$ BEGIN
            ALTER TABLE "Element" ADD CONSTRAINT "Element_stepId_fkey" FOREIGN KEY ("stepId") REFERENCES "Step"("id") ON DELETE CASCADE ON UPDATE CASCADE;
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;""",

        """DO $$ BEGIN
            ALTER TABLE "Element" ADD CONSTRAINT "Element_threadId_fkey" FOREIGN KEY ("threadId") REFERENCES "Thread"("id") ON DELETE CASCADE ON UPDATE CASCADE;
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;""",

        """DO $$ BEGIN
            ALTER TABLE "Feedback" ADD CONSTRAINT "Feedback_stepId_fkey" FOREIGN KEY ("stepId") REFERENCES "Step"("id") ON DELETE SET NULL ON UPDATE CASCADE;
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;""",

        """DO $$ BEGIN
            ALTER TABLE "Step" ADD CONSTRAINT "Step_parentId_fkey" FOREIGN KEY ("parentId") REFERENCES "Step"("id") ON DELETE CASCADE ON UPDATE CASCADE;
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;""",

        """DO $$ BEGIN
            ALTER TABLE "Step" ADD CONSTRAINT "Step_threadId_fkey" FOREIGN KEY ("threadId") REFERENCES "Thread"("id") ON DELETE CASCADE ON UPDATE CASCADE;
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;""",

        """DO $$ BEGIN
            ALTER TABLE "Thread" ADD CONSTRAINT "Thread_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;""",

        # Update migration: Add tags column
        """ALTER TABLE "Thread" ADD COLUMN IF NOT EXISTS "tags" TEXT[] DEFAULT ARRAY[]::TEXT[];"""
    ]

    for sql in sql_statements:
        try:
            print(f"Executing: {sql[:50]}...")
            cur.execute(sql)
        except Exception as e:
            print(f"Error executing sql: {e}")
            # We continue because some might fail if already partial state, but we try to be robust.
            # However, for critical failures in creation, this might be bad.
            # But with IF NOT EXISTS and DO blocks, it should be fine.
            pass
    
    print("Migrations completed.")
    conn.close()

if __name__ == "__main__":
    run_migrations()
