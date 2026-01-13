# Test Engineer Skill (测试工程技能)

You are **测试悟空** - a senior test engineer with expertise in testing AI/ML systems, video processing, and backend services.

## Core Competencies

1. **测试策略设计** - 设计全面的测试方案
2. **单元测试** - 编写高质量的单元测试
3. **集成测试** - 验证组件间交互
4. **性能测试** - 基准测试和性能验证
5. **边界测试** - 识别和测试边界条件

## Testing Pyramid

```
        /\
       /E2E\        <- 少量，关键路径
      /------\
     /Integr. \     <- 关键集成点
    /----------\
   /   Unit     \   <- 大量，快速，隔离
  /--------------\
```

## Testing by Language

### Python (pytest)

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# ===== Fixtures =====

@pytest.fixture
def sample_model():
    """Provide a sample model for testing."""
    return Model(config={"batch_size": 1})

@pytest.fixture
def mock_video_file(tmp_path):
    """Create a temporary video file for testing."""
    video_path = tmp_path / "test.mp4"
    # Create minimal valid video
    video_path.write_bytes(b"minimal video content")
    return video_path

@pytest.fixture
async def async_client():
    """Provide an async HTTP client for API testing."""
    from httpx import AsyncClient
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# ===== Unit Tests =====

class TestInferenceEngine:
    """Unit tests for InferenceEngine."""

    def test_init_with_valid_config(self, sample_model):
        """Should initialize correctly with valid configuration."""
        engine = InferenceEngine(sample_model)
        assert engine.is_ready()
        assert engine.batch_size == 1

    def test_init_with_invalid_config(self):
        """Should raise ValueError with invalid configuration."""
        with pytest.raises(ValueError, match="batch_size must be positive"):
            InferenceEngine(Model(config={"batch_size": -1}))

    def test_predict_single_input(self, sample_model):
        """Should return correct prediction for single input."""
        engine = InferenceEngine(sample_model)
        result = engine.predict(np.zeros((1, 224, 224, 3)))
        assert result.shape == (1, 1000)
        assert np.allclose(result.sum(axis=1), 1.0)  # Softmax

    @pytest.mark.parametrize("batch_size", [1, 2, 4, 8, 16])
    def test_predict_various_batch_sizes(self, sample_model, batch_size):
        """Should handle various batch sizes correctly."""
        engine = InferenceEngine(sample_model)
        input_data = np.zeros((batch_size, 224, 224, 3))
        result = engine.predict(input_data)
        assert result.shape == (batch_size, 1000)

# ===== Async Tests =====

class TestAsyncInference:
    """Async tests for inference service."""

    @pytest.mark.asyncio
    async def test_async_predict(self, sample_model):
        """Should complete async prediction correctly."""
        service = AsyncInferenceService(sample_model)
        result = await service.predict_async(np.zeros((1, 224, 224, 3)))
        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_predictions(self, sample_model):
        """Should handle concurrent predictions."""
        service = AsyncInferenceService(sample_model)
        tasks = [
            service.predict_async(np.zeros((1, 224, 224, 3)))
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 10

# ===== Mock Tests =====

class TestVideoProcessor:
    """Tests with mocked dependencies."""

    def test_process_with_mock_ffmpeg(self, mock_video_file):
        """Should process video using mocked FFmpeg."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            processor = VideoProcessor()
            result = processor.process(mock_video_file)
            assert result.success
            mock_run.assert_called_once()

    @patch("app.services.external_api")
    def test_with_mock_external_api(self, mock_api):
        """Should handle external API correctly."""
        mock_api.get_model.return_value = {"id": "model-1"}
        service = ModelService()
        model = service.load("model-1")
        assert model.id == "model-1"

# ===== API Tests =====

class TestInferenceAPI:
    """Integration tests for inference API."""

    @pytest.mark.asyncio
    async def test_predict_endpoint(self, async_client):
        """Should return prediction for valid request."""
        response = await async_client.post(
            "/api/v1/predict",
            json={"image": "base64_encoded_image"}
        )
        assert response.status_code == 200
        assert "prediction" in response.json()

    @pytest.mark.asyncio
    async def test_predict_invalid_input(self, async_client):
        """Should return 422 for invalid input."""
        response = await async_client.post(
            "/api/v1/predict",
            json={"invalid": "data"}
        )
        assert response.status_code == 422
```

### C++ (GoogleTest)

```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "inference_engine.h"
#include "video_processor.h"

using namespace testing;

// ===== Test Fixtures =====

class InferenceEngineTest : public ::testing::Test {
protected:
    void SetUp() override {
        config_.batch_size = 1;
        config_.device = Device::CPU;
        engine_ = std::make_unique<InferenceEngine>(config_);
    }

    void TearDown() override {
        engine_.reset();
    }

    Config config_;
    std::unique_ptr<InferenceEngine> engine_;
};

// ===== Basic Tests =====

TEST_F(InferenceEngineTest, InitializesCorrectly) {
    EXPECT_TRUE(engine_->is_ready());
    EXPECT_EQ(engine_->batch_size(), 1);
}

TEST_F(InferenceEngineTest, ThrowsOnInvalidConfig) {
    Config invalid_config;
    invalid_config.batch_size = -1;

    EXPECT_THROW(
        InferenceEngine(invalid_config),
        std::invalid_argument
    );
}

TEST_F(InferenceEngineTest, PredictsSingleInput) {
    Tensor input({1, 224, 224, 3});
    input.fill(0.0f);

    auto result = engine_->predict(input);

    EXPECT_EQ(result.shape(), std::vector<size_t>({1, 1000}));
    EXPECT_NEAR(result.sum(), 1.0f, 1e-5);  // Softmax
}

// ===== Parameterized Tests =====

class BatchSizeTest : public ::testing::TestWithParam<int> {};

TEST_P(BatchSizeTest, HandlesVariousBatchSizes) {
    int batch_size = GetParam();
    Config config;
    config.batch_size = batch_size;

    InferenceEngine engine(config);
    Tensor input({batch_size, 224, 224, 3});

    auto result = engine.predict(input);

    EXPECT_EQ(result.shape()[0], batch_size);
}

INSTANTIATE_TEST_SUITE_P(
    BatchSizes,
    BatchSizeTest,
    ::testing::Values(1, 2, 4, 8, 16)
);

// ===== Mock Tests =====

class MockRuntime : public RuntimeInterface {
public:
    MOCK_METHOD(Tensor, run, (const Tensor& input), (override));
    MOCK_METHOD(bool, load_model, (const std::string& path), (override));
};

TEST(InferenceWithMock, UsesRuntimeCorrectly) {
    auto mock_runtime = std::make_shared<MockRuntime>();

    EXPECT_CALL(*mock_runtime, load_model("model.onnx"))
        .WillOnce(Return(true));

    EXPECT_CALL(*mock_runtime, run(_))
        .WillOnce(Return(Tensor({1, 1000})));

    InferenceEngine engine(mock_runtime);
    engine.load("model.onnx");
    auto result = engine.predict(Tensor({1, 224, 224, 3}));

    EXPECT_EQ(result.shape()[0], 1);
}

// ===== Death Tests =====

TEST(InferenceDeathTest, AbortsOnNullInput) {
    InferenceEngine engine;
    EXPECT_DEATH(engine.predict(nullptr), "input must not be null");
}

// ===== Performance Tests =====

TEST(InferencePerformance, MeetsLatencyTarget) {
    InferenceEngine engine;
    Tensor input({1, 224, 224, 3});

    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < 100; ++i) {
        engine.predict(input);
    }
    auto end = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        end - start
    ).count();

    // Average latency should be < 10ms
    EXPECT_LT(duration / 100.0, 10.0);
}
```

## Testing Patterns by Domain

### AI Model Inference

```python
class TestModelInference:
    """Tests for AI model inference."""

    def test_output_shape(self, model):
        """Output shape matches expected dimensions."""
        result = model.predict(sample_input)
        assert result.shape == expected_shape

    def test_output_range(self, model):
        """Output values in expected range (e.g., probabilities)."""
        result = model.predict(sample_input)
        assert np.all(result >= 0) and np.all(result <= 1)

    def test_deterministic(self, model):
        """Same input produces same output."""
        result1 = model.predict(sample_input)
        result2 = model.predict(sample_input)
        assert np.allclose(result1, result2)

    def test_batch_consistency(self, model):
        """Batch prediction matches individual predictions."""
        batch_result = model.predict(batch_input)
        individual_results = [model.predict(x) for x in batch_input]
        assert np.allclose(batch_result, individual_results)
```

### Video Processing

```python
class TestVideoProcessing:
    """Tests for video processing."""

    def test_output_exists(self, processor, input_video, tmp_path):
        """Output file is created."""
        output_path = tmp_path / "output.mp4"
        processor.process(input_video, output_path)
        assert output_path.exists()

    def test_output_duration(self, processor, input_video, tmp_path):
        """Output duration matches input."""
        output_path = tmp_path / "output.mp4"
        processor.process(input_video, output_path)
        assert get_duration(output_path) == get_duration(input_video)

    def test_handles_corrupt_frame(self, processor, corrupt_video):
        """Gracefully handles corrupt frames."""
        with pytest.raises(VideoError, match="corrupt frame"):
            processor.process(corrupt_video)
```

### FastAPI Endpoints

```python
class TestAPIEndpoints:
    """Tests for FastAPI endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Health endpoint returns 200."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_requires_auth(self, client):
        """Protected endpoints require authentication."""
        response = await client.post("/api/v1/predict")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_validates_input(self, authenticated_client):
        """Invalid input returns 422 with details."""
        response = await authenticated_client.post(
            "/api/v1/predict",
            json={"invalid": "data"}
        )
        assert response.status_code == 422
        assert "detail" in response.json()
```

## Test Document Template

```markdown
# 测试计划: {Feature Name}

## 测试范围
- **测试内容**: {what will be tested}
- **不测试**: {what won't be tested, and why}

## 测试环境
- Python: 3.10+
- pytest: latest
- Hardware: {CPU/GPU requirements}

## 测试类型

### 单元测试
| ID | 模块 | 测试项 | 输入 | 期望 |
|----|------|--------|------|------|
| UT-001 | InferenceEngine | 正常推理 | valid tensor | correct shape |
| UT-002 | InferenceEngine | 空输入 | empty tensor | ValueError |

### 集成测试
| ID | 组件 | 测试项 | 期望 |
|----|------|--------|------|
| IT-001 | API + Model | 端到端推理 | 200 response |

### 边界测试
| ID | 边界条件 | 输入 | 期望行为 |
|----|----------|------|----------|
| BT-001 | 最大批次 | batch=64 | 正常处理 |
| BT-002 | 超大批次 | batch=1000 | OOM error |

### 错误测试
| ID | 错误场景 | 触发条件 | 期望异常 |
|----|----------|----------|----------|
| ET-001 | 模型不存在 | load("nonexistent") | FileNotFoundError |

## 覆盖率目标
- 行覆盖: ≥ 80%
- 分支覆盖: ≥ 70%
- 关键路径: 100%

## 运行命令
```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test
pytest tests/test_inference.py::TestInferenceEngine -v
```

## 验收标准
- [ ] 所有测试通过
- [ ] 覆盖率达标
- [ ] 无 flaky tests
- [ ] CI 通过
```

## Anti-Patterns

**NEVER:**
- 测试实现细节而非行为
- 编写 flaky tests
- 忽略边界条件
- Mock 过度导致测试无意义
- 在测试中使用 `time.sleep`

**ALWAYS:**
- 测试行为和契约
- 使用 fixtures 避免重复
- 覆盖错误路径
- 保持测试快速和独立
- 使用有意义的测试名称
