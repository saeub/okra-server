Vue.component("experiment-form", {
  template: `
    <ul>
      <li>ID: <input type="text" v-model="data.id" @input="emitData()" disabled></li>
      <li>Title: <input type="text" v-model="data.title" @input="emitData()"></li>
      <li>Instructions: <textarea v-model="data.instructions" @input="emitData()"></textarea></li>
      <li>
        Practice task:
        <input type="checkbox" v-model="hasPracticeTask">
        <task v-if="data.practiceTask !== null" v-model="data.practiceTask" @input="emitData()"></task>
      </li>
      <li>
        Tasks:
        <ul>
          <li v-for="(task, i) in data.tasks" :key="'task-' + task.key">
            <input type="button" value="Remove task" @click="removeTask(i)">
            <task v-model="data.tasks[i]"></task>
          </li>
        </ul>
        <input type="button" value="Add task" @click="addTask()">
      </li>
      <li>
        Assignments:
        <ul>
          <li v-for="assignment in data.assignments" :key="'participant-' + assignment.participant">
            <task-assignments :participant="assignment.participant" :tasks="data.tasks" v-model="assignment.tasks"></task-assignments>
          </li>
        </ul>
      </li>
    </ul>
  `,

  props: {
    value: {
      type: Object,
      required: true,
    },
  },

  data() {
    const data = { ...this.value };
    const hasPracticeTask = data.practiceTask !== null;
    let taskKeyCounter = 0;
    for (task of data.tasks) {
      task.key = taskKeyCounter;
      taskKeyCounter++;
    }
    return {
      data: { ...this.value },
      taskKeyCounter,
      hasPracticeTask,
    };
  },

  methods: {
    addTask() {
      this.data.tasks.push({
        id: uuidv4(),
        key: this.taskKeyCounter,
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

    emitData() {
      this.$emit("input", this.data);
    },
  },

  watch: {
    hasPracticeTask(newHasPracticeTask) {
      if (newHasPracticeTask) {
        this.data.practiceTask = {
          id: uuidv4(),
          label: `practice-task`,
          data: {},
        };
      } else {
        this.data.practiceTask = null;
      }
      this.emitData();
    },
  },
});

Vue.component("task", {
  template: `
    <ul>
      <li>ID: <input type="text" v-model="task.id" @input="emitData()" disabled></li>
      <li>Label: <input type="text" v-model="task.label" @input="emitData()"></li>
      <li>Data: <json-editor v-model="task.data" @input="emitData()"></json-editor></li>
    </ul>
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

Vue.component("json-editor", {
  template: `
    <div>
      <textarea v-model="text" @input="validate()">{{ text }}</textarea>
      <div v-if="error !== null" style="color: red">
        {{ error }}
      </div>
      <div v-else style="color: green">
        Valid.
      </div>
    </div>
  `,

  props: {
    value: {
      type: undefined,
      required: true,
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
      }
    },
  },
});

Vue.component("task-assignments", {
  template: `
    <div>
      {{ participant }}
      <select v-for="(taskId, i) in taskIds" :value="taskIds[i]" @input="onInput(i, $event.target.value)">
        <option value="DELETED">- DELETE -</option>
        <option v-for="task in tasks" :key="task.id" :value="task.id">{{ task.label }}</option>
      </select>
      <input type="button" value="+" @click="addTask()" :disabled="getFreeTaskId() === null">
    </div>
  `,

  props: {
    participant: {
      type: String,
      required: true,
    },
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
      taskIds: [...this.value],
    };
  },

  methods: {
    getFreeTaskId() {
      for (const task of this.tasks) {
        if (this.taskIds.indexOf(task.id) === -1) {
          return task.id;
        }
      }
      return null;
    },

    addTask() {
      const freeId = this.getFreeTaskId();
      if (freeId !== null) {
        this.taskIds.push(freeId);
      }
      this.emitData();
    },

    onInput(index, value) {
      if (value === "DELETED") {
        this.taskIds.splice(index, 1);
      } else {
        this.taskIds[index] = value;
      }
      this.emitData();
    },

    emitData() {
      this.$emit("input", this.taskIds);
    },
  },

  watch: {
    tasks(newTasks) {
      const newTaskIds = [];
      for (task of newTasks) {
        newTaskIds.push(task.id);
      }
      for (let i = 0; i < this.taskIds.length; i++) {
        if (newTaskIds.indexOf(this.taskIds[i]) === -1) {
          this.taskIds.splice(i, 1);
          i--;
        }
      }
      this.emitData();
    },
  },
});
