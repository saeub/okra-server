Vue.component("experiment-form", {
  template: `
    <div>
      <div class="row">
        <div class="col">
          <h1>Experiment "{{ data.title }}"</h1>
        </div>
        <div class="col-auto">
          <input class="form-control" type="file" @change="loadFile">
        </div>
      </div>
      <div class="input-group mb-2">
        <span class="input-group-text">ID</span>
        <input type="text" class="form-control" v-model="data.id" @input="emitData()" disabled>
      </div>
      <div class="form-floating mb-2">
        <select class="form-select" v-model="data.taskType" @input="emitData()">
          <option v-for="(typeName, typeId) in taskTypeChoices" :value="typeId">
            {{ typeName }}
          </option>
        </select>
        <label>Task type</label>
      </div>
      <div class="form-floating mb-2">
        <input type="text" class="form-control" v-model="data.title" @input="emitData()">
        <label>Title</label>
      </div>
      <div class="form-floating mb-2">
        <textarea class="form-control" style="height: 100px" v-model="data.instructions" @input="emitData()"></textarea>
        <label>Instructions before task</label>
      </div>
      <div class="form-floating mb-2">
        <textarea class="form-control" style="height: 100px" v-model="data.instructionsAfterTask" @input="emitData()"></textarea>
        <label>Instructions after each task</label>
      </div>
      <div class="form-floating mb-2">
        <textarea class="form-control" style="height: 100px" v-model="data.instructionsAfterFinalTask" @input="emitData()"></textarea>
        <label>Instructions after final task</label>
      </div>
      <section class="mb-2">
        <h2>
          Practice task
          <button type="button" class="btn btn-outline-primary btn-sm" v-if="data.practiceTask === null" @click="addPracticeTask()"><i class="bi bi-plus"></i></button>
          <button type="button" class="btn btn-outline-danger btn-sm" v-else @click="removePracticeTask()"><i class="bi bi-trash-fill"></i></button>
        </h2>
        <task v-if="data.practiceTask !== null" v-model="data.practiceTask" @input="emitData()"></task>
        <div v-if="data.practiceTask !== null" class="form-floating mb-2">
          <textarea class="form-control" style="height: 100px" v-model="data.instructionsAfterPracticeTask" @input="emitData()"></textarea>
          <label>Instructions after practice task</label>
        </div>
      </section>
      <section class="mb-2">
        <h2>Tasks</h2>
        <div class="accordion mb-2">
          <div class="accordion-item" v-for="(task, i) in data.tasks" :key="'task-' + task.id">
            <h3 class="accordion-header">
              <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" :data-bs-target="'#task-collapse-' + task.id">
                <button type="button" class="btn btn-outline-danger btn-sm me-2" @click="removeTask(i)"><i class="bi bi-trash-fill"></i></button>
                {{ task.label }}
              </button>
            </h3>
            <div class="accordion-collapse collapse hide" :id="'task-collapse-' + task.id">
              <div class="accordion-body">
                <task v-model="data.tasks[i]"></task>
              </div>
            </div>
          </div>
        </div>
        <button type="button" class="btn btn-outline-primary" @click="addTask()"><i class="bi bi-plus"></i></button>
      </section>
      <section class="mb-2">
        <h2>Task ratings</h2>
        <div class="accordion mb-2">
          <div class="accordion-item" v-for="(rating, i) in data.ratings" :key="'rating-' + rating.id">
            <h3 class="accordion-header">
              <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" :data-bs-target="'#rating-collapse-' + rating.id">
                <button type="button" class="btn btn-outline-danger btn-sm me-2" @click="removeRating(i)"><i class="bi bi-trash-fill"></i></button>
                {{ rating.question }}
              </button>
            </h3>
            <div class="accordion-collapse collapse hide" :id="'rating-collapse-' + rating.id">
              <div class="accordion-body">
                <rating :rating-type-choices="ratingTypeChoices" v-model="data.ratings[i]"></rating>
              </div>
            </div>
          </div>
        </div>
        <button type="button" class="btn btn-outline-primary" value="Add rating" @click="addRating()"><i class="bi bi-plus"></i></button>
      </section>
      <section>
        <h2>Assignments</h2>
        <ul class="list-group">
          <li class="list-group-item" v-for="(label, id) in participantLabels" :key="'participant-' + id">
            <h3 class="h6">Participant: {{ label }} ({{ id }})</h3>
            <task-assignments :tasks="data.tasks" v-model="data.assignments[id]"></task-assignments>
          </li>
        </ul>
      </section>
    </div>
  `,

  props: {
    value: {
      type: Object,
      required: true,
    },
    taskTypeChoices: {
      type: Object,
      required: true,
    },
    ratingTypeChoices: {
      type: Object,
      required: true,
    },
    participantLabels: {
      type: Object,
      required: true,
    },
  },

  data() {
    const data = { ...this.value };
    const hasPracticeTask = data.practiceTask !== null;
    let taskKeyCounter = data.tasks.length;
    return {
      data: { ...this.value },
      taskKeyCounter,
      hasPracticeTask,
    };
  },

  methods: {
    loadFile(event) {
      const file = event.target.files[0];
      const reader = new FileReader();
      reader.onload = (event) => {
        const id = this.data.id;
        this.data = JSON.parse(event.target.result);
        this.data.id = id;
        this.emitData();
      };
      reader.readAsText(file);
    },

    addPracticeTask() {
      this.data.practiceTask = {
        id: uuidv4(),
        label: `practice-task`,
        data: {},
      };
      this.emitData();
    },

    removePracticeTask() {
      this.data.practiceTask = null;
      this.emitData();
    },

    addTask() {
      this.data.tasks.push({
        id: uuidv4(),
        label: `task-${this.taskKeyCounter}`,
        data: {},
      });
      this.taskKeyCounter++;
      this.emitData();
    },

    removeTask(index) {
      this.data.tasks.splice(index, 1);
      this.emitData();
    },

    addRating() {
      this.data.ratings.push({
        id: uuidv4(),
        question: "",
        type: "emoticon",
        lowExtreme: null,
        highExtreme: null,
      });
      this.emitData();
    },

    removeRating(index) {
      this.data.ratings.splice(index, 1);
      this.emitData();
    },

    emitData() {
      this.$emit("input", this.data);
    },
  },
});

Vue.component("task", {
  template: `
    <div>
      <div class="input-group mb-2">
        <span class="input-group-text">ID</span>
        <input type="text" class="form-control" v-model="task.id" @input="emitData()" disabled>
      </div>
      <div class="form-floating mb-2">
        <input type="text" class="form-control" v-model="task.label" @input="emitData()">
        <label>Label</label>
      </div>
      <json-editor class="mb-2" v-model="task.data" @input="emitData()"></json-editor>
    </div>
  `,

  props: {
    value: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      task: { ...this.value },
    };
  },

  methods: {
    emitData() {
      this.$emit("input", this.task);
    },
  },
});

Vue.component("rating", {
  template: `
    <div>
      <div class="input-group mb-2">
        <span class="input-group-text">ID</span>
        <input type="rating" class="form-control" v-model="rating.id" @input="emitData()" disabled>
      </div>
      <div class="form-floating mb-2">
        <input type="text" class="form-control" v-model="rating.question" @input="emitData()">
        <label>Question</label>
      </div>
      <div class="form-floating mb-2">
        <select class="form-select" v-model="rating.type" @input="emitData()">
          <option v-for="(typeName, typeId) in ratingTypeChoices" :value="typeId">
            {{ typeName }}
          </option>
        </select>
        <label>Type</label>
      </div>
      <div class="container">
        <div class="row row-cols-2">
          <div class="col ps-0 pe-1">
            <div class="form-floating">
              <input type="text" class="form-control" v-model="rating.lowExtreme" @input="emitData()">
              <label>Low extreme</label>
            </div>
          </div>
          <div class="col pe-0 ps-1">
            <div class="form-floating">
              <input type="text" class="form-control" v-model="rating.highExtreme" @input="emitData()">
              <label>High extreme</label>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,

  props: {
    value: {
      type: Object,
      required: true,
    },
    ratingTypeChoices: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      rating: { ...this.value },
    };
  },

  methods: {
    emitData() {
      this.$emit("input", this.rating);
    },
  },
});

Vue.component("json-editor", {
  template: `
    <div class="form-floating">
      <textarea :class="{'form-control': true, 'is-invalid': error !== null}" style="height: 150px" v-model="text" @input="validate()">{{ text }}</textarea>
      <label>{{ label }}</label>
      <div class="alert alert-danger" v-if="error !== null" style="color: red">
        {{ error }}
      </div>
    </div>
  `,

  props: {
    value: {
      type: undefined,
      required: true,
    },
    label: {
      type: String,
      default: "Data",
    },
  },

  data() {
    return {
      text: JSON.stringify(this.value),
      error: null,
    };
  },

  methods: {
    validate() {
      try {
        const data = JSON.parse(this.text);
        this.error = null;
        this.$emit("input", data);
      } catch (e) {
        this.error = e;
        this.$emit("input", null);
      }
    },
  },
});

Vue.component("task-assignments", {
  template: `
    <div class="input-group">
      <select class="form-select" style="flex: unset; width: unset" v-for="(assignment, i) in assignments" :value="assignments[i].id" @input="onInput(i, $event.target.value)" :disabled="assignment.started">
        <option value="DELETED">- DELETE -</option>
        <option v-for="task in tasks" :key="task.id" :value="task.id">{{ task.label }}</option>
      </select>
      <button type="button" class="btn btn-outline-primary" @click="addTask()" :disabled="getAvailableAssignment() === null"><i class="bi bi-plus"></i></button>
    </div>
  `,

  props: {
    tasks: {
      type: Array,
      required: true,
    },
    value: {
      type: Array,
      required: true,
    },
  },

  data() {
    return {
      assignments: [...this.value],
    };
  },

  methods: {
    getAvailableAssignment() {
      for (const task of this.tasks) {
        var taken = false;
        for (const assignment of this.assignments) {
          if (assignment.id == task.id) {
            taken = true;
            break;
          }
        }
        if (!taken) {
          return {
            id: task.id,
            started: false,
          };
        }
      }
      return null;
    },

    addTask() {
      const availableAssignment = this.getAvailableAssignment();
      if (availableAssignment !== null) {
        this.assignments.push(availableAssignment);
      }
      this.emitData();
    },

    onInput(index, value) {
      if (value === "DELETED") {
        this.assignments.splice(index, 1);
      } else {
        this.assignments[index] = { id: value, started: false };
      }
      this.emitData();
    },

    emitData() {
      this.$emit("input", this.assignments);
    },
  },

  watch: {
    tasks(newTasks) {
      const newTaskIds = [];
      for (task of newTasks) {
        newTaskIds.push(task.id);
      }
      for (let i = 0; i < this.assignments.length; i++) {
        if (newTaskIds.indexOf(this.assignments[i].id) === -1) {
          this.assignments.splice(i, 1);
          i--;
        }
      }
      this.emitData();
    },
  },
});
