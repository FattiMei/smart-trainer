#include "TensorFlowLite.h"

#include "model.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_log.h"
//#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/micro/system_setup.h"
#include "tensorflow/lite/schema/schema_generated.h"

// Globals, used for compatibility with Arduino-style sketches.
namespace {
  const tflite::Model* model = nullptr;
  tflite::MicroInterpreter* interpreter = nullptr;
  TfLiteTensor* model_input = nullptr;

  // Create an area of memory to use for input, output, and intermediate arrays.
  // The size of this will depend on the model you're using, and may need to be
  // determined by experimentation.
  constexpr int kTensorArenaSize = 64 * 1024;
  // Keep aligned to 16 bytes for CMSIS
  alignas(16) uint8_t tensor_arena[kTensorArenaSize];
}  // namespace

void setup() {
  tflite::InitializeTarget();

  // Map the model into a usable data structure. This doesn't involve any
  // copying or parsing, it's a very lightweight operation.
  model = tflite::GetModel(g_model);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    MicroPrintf("Model provided is schema version %d not equal to supported version %d.",
                model->version(), TFLITE_SCHEMA_VERSION);
    return;
  }

  // Pull in only the operation implementations we need.
  // This relies on a complete list of all the ops needed by this graph.
  // An easier approach is to just use the AllOpsResolver, but this will
  // incur some penalty in code space for op implementations that are not
  // needed by this graph.
  //
  // tflite::AllOpsResolver resolver;
  // NOLINTNEXTLINE(runtime-global-variables)
  static tflite::MicroMutableOpResolver<6> micro_op_resolver;
  if (micro_op_resolver.AddConv2D() != kTfLiteOk) { 
    return; 
  }
  if (micro_op_resolver.AddMaxPool2D() != kTfLiteOk) { 
    return; 
  }
  if (micro_op_resolver.AddFullyConnected() != kTfLiteOk) { 
    return; 
  }
  if (micro_op_resolver.AddReshape() != kTfLiteOk) {
    return;
  }
  if (micro_op_resolver.AddRelu() != kTfLiteOk) {
    return; 
  }
  if (micro_op_resolver.AddLogistic() != kTfLiteOk) { 
    return;
  }

  // Build an interpreter to run the model with.
  static tflite::MicroInterpreter static_interpreter(
      model, micro_op_resolver, tensor_arena, kTensorArenaSize);
  interpreter = &static_interpreter;

  // Allocate memory from the tensor_arena for the model's tensors.
  TfLiteStatus allocate_status = interpreter->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    MicroPrintf("AllocateTensors() failed");
    return;
  } 

  // Obtain pointers to the model's input tensors.
  model_input = interpreter->input(0);

  MicroPrintf("Initialization complete");
}

void loop() {
   // 1) Prepare dummy input quantized zero matrix
  if (model_input->type == kTfLiteInt8) {
    int8_t* input_buffer = interpreter->typed_input_tensor<int8_t>(0);
    const int input_elements = model_input->bytes; // int8 -> bytes == elementi
    const float scale = model_input->params.scale;
    const int32_t zero_point = model_input->params.zero_point;

    // Quantized value corresponding to 0.0f
    int32_t q = (int32_t)round(0.0f / scale) + zero_point;
    if (q < -128) q = -128;
    if (q > 127) q = 127;
    int8_t q8 = static_cast<int8_t>(q);
    for (int i = 0; i < input_elements; ++i) {
      input_buffer[i] = q8;
    }
  }
  else if (model_input->type == kTfLiteFloat32) {
    float* input_buffer = interpreter->typed_input_tensor<float>(0);
    const int input_elements = model_input->bytes / sizeof(float);
    for (int i = 0; i < input_elements; ++i) {
      input_buffer[i] = 0.0f;
    }
  } else {
    MicroPrintf("Unsupported input tensor type: %d\n", model_input->type);
    delay(1000);
    return;
  }

  // 2) Measure time and invoke the model
  uint32_t t_start = millis();
  TfLiteStatus invoke_status = interpreter->Invoke();
  uint32_t t_end = millis();
  uint32_t infer_ms = t_end - t_start;

  if (invoke_status != kTfLiteOk) {
    MicroPrintf("Invoke() fallita");
    delay(500);
    return;
  }

  // 3) Print inference time
  MicroPrintf("Inference time: %d ms\n", (unsigned long)infer_ms);

  // Inference cycle
  delay(1000);
}